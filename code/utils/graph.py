"""
DAG (Directed Acyclic Graph) operations for topology workflows.

Provides TopologyGraph class for:
- Cycle detection
- Topological sorting
- Parallel execution group identification
- Dependency resolution
"""

from typing import List, Dict, Set, Tuple, Optional
import networkx as nx


class TopologyGraph:
    """Represents a topology workflow as a directed acyclic graph."""

    def __init__(self, steps: List[Dict]):
        """
        Initialize graph from topology steps.

        Args:
            steps: List of step dictionaries from topology.yaml
        """
        self.steps = {step['step']: step for step in steps}
        self.graph = nx.DiGraph()

        # Add nodes
        for step_id in self.steps.keys():
            self.graph.add_node(step_id)

        # Add edges from dependencies
        for step_id, step in self.steps.items():
            depends_on = step.get('depends_on', [])
            for dependency in depends_on:
                self.graph.add_edge(dependency, step_id)

    def has_cycle(self) -> Tuple[bool, Optional[List[str]]]:
        """
        Check if graph has cycles.

        Returns:
            Tuple of (has_cycle, cycle_path)
            cycle_path is None if no cycle found
        """
        try:
            cycle = nx.find_cycle(self.graph, orientation='original')
            cycle_path = [edge[0] for edge in cycle]
            cycle_path.append(cycle[0][0])  # Close the cycle
            return True, cycle_path
        except nx.NetworkXNoCycle:
            return False, None

    def topological_sort(self) -> List[str]:
        """
        Get topological sort of steps (execution order).

        Returns:
            List of step IDs in execution order

        Raises:
            ValueError: If graph has cycles
        """
        has_cycle, cycle_path = self.has_cycle()
        if has_cycle:
            raise ValueError(f"Graph has cycle: {' -> '.join(cycle_path)}")

        return list(nx.topological_sort(self.graph))

    def get_dependencies(self, step_id: str) -> List[str]:
        """
        Get all dependencies for a step (transitive closure).

        Args:
            step_id: Step to get dependencies for

        Returns:
            List of step IDs this step depends on (directly or indirectly)
        """
        return list(nx.ancestors(self.graph, step_id))

    def get_dependents(self, step_id: str) -> List[str]:
        """
        Get all steps that depend on this step.

        Args:
            step_id: Step to get dependents for

        Returns:
            List of step IDs that depend on this step
        """
        return list(nx.descendants(self.graph, step_id))

    def get_parallel_groups(self) -> List[List[str]]:
        """
        Get groups of steps that can execute in parallel.

        Returns:
            List of groups, where each group is a list of step IDs
            that can execute in parallel
        """
        sorted_steps = self.topological_sort()
        groups = []
        processed = set()

        while len(processed) < len(sorted_steps):
            # Find all steps whose dependencies are satisfied
            parallel_group = []
            for step_id in sorted_steps:
                if step_id in processed:
                    continue

                dependencies = set(self.graph.predecessors(step_id))
                if dependencies.issubset(processed):
                    parallel_group.append(step_id)

            if parallel_group:
                groups.append(parallel_group)
                processed.update(parallel_group)
            else:
                # Should not happen if graph is acyclic
                break

        return groups

    def get_execution_levels(self) -> Dict[str, int]:
        """
        Get execution level for each step.

        Level 0 = entry points (no dependencies)
        Level N = depends on steps at level N-1

        Returns:
            Dict mapping step_id to execution level
        """
        levels = {}
        for step_id in nx.topological_sort(self.graph):
            predecessors = list(self.graph.predecessors(step_id))
            if not predecessors:
                levels[step_id] = 0
            else:
                levels[step_id] = max(levels[pred] for pred in predecessors) + 1
        return levels

    def get_critical_path(self) -> List[str]:
        """
        Get critical path (longest path through graph).

        Returns:
            List of step IDs in critical path
        """
        levels = self.get_execution_levels()
        max_level = max(levels.values())

        # Find step at max level
        end_steps = [step for step, level in levels.items() if level == max_level]

        # Trace back to find longest path
        paths = []
        for end_step in end_steps:
            path = [end_step]
            current = end_step

            while levels[current] > 0:
                # Find predecessor with max level
                predecessors = list(self.graph.predecessors(current))
                if predecessors:
                    pred_with_max_level = max(predecessors, key=lambda p: levels[p])
                    path.insert(0, pred_with_max_level)
                    current = pred_with_max_level
                else:
                    break

            paths.append(path)

        # Return longest path
        return max(paths, key=len) if paths else []

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate graph structure.

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        # Check for cycles
        has_cycle, cycle_path = self.has_cycle()
        if has_cycle:
            errors.append(f"Graph has cycle: {' -> '.join(cycle_path)}")

        # Check for orphaned nodes (no path from any entry point)
        entry_points = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        reachable = set()
        for entry in entry_points:
            reachable.update(nx.descendants(self.graph, entry))
            reachable.add(entry)

        orphaned = set(self.graph.nodes()) - reachable
        if orphaned:
            errors.append(f"Orphaned steps (no path from entry points): {', '.join(orphaned)}")

        # Check for missing dependencies
        for step_id, step in self.steps.items():
            depends_on = step.get('depends_on', [])
            for dep in depends_on:
                if dep not in self.steps:
                    errors.append(f"Step '{step_id}' depends on undefined step '{dep}'")

        return len(errors) == 0, errors

    @classmethod
    def from_yaml(cls, topology_dict: Dict) -> 'TopologyGraph':
        """
        Create TopologyGraph from parsed topology.yaml.

        Args:
            topology_dict: Parsed topology YAML

        Returns:
            TopologyGraph instance
        """
        workflow = topology_dict.get('topology', {}).get('workflow', [])
        return cls(workflow)
