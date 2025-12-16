#!/usr/bin/env python3
"""
Simple Elyra Pipeline Generator for UH2025Agent
Generates a .pipeline file from topology.yaml without complex dependencies
"""

import json
import yaml
import uuid
from pathlib import Path


def generate_elyra_pipeline(topology_path, output_path):
    """Generate Elyra pipeline from topology.yaml"""

    # Load topology
    with open(topology_path, 'r') as f:
        topology_dict = yaml.safe_load(f)

    topology = topology_dict.get('topology', {})
    workflow = topology.get('workflow', [])
    modules = {m['id']: m for m in topology.get('modules', [])}

    # Create Elyra pipeline structure
    # Use single UUID for all pipeline IDs (Elyra v3.0 requirement)
    pipeline_id = str(uuid.uuid4())

    pipeline = {
        "doc_type": "pipeline",
        "version": "3.0",
        "json_schema": "http://api.dataplatform.ibm.com/schemas/common-pipeline/pipeline-flow/pipeline-flow-v3-schema.json",
        "id": pipeline_id,
        "primary_pipeline": pipeline_id,
        "pipelines": [{
            "id": pipeline_id,
            "runtime": "Generic",
            "runtime_ref": "",
            "nodes": [],
            "app_data": {
                "ui_data": {
                    "comments": []
                },
                "version": 8,
                "properties": {
                    "name": topology.get('name', 'UH2025Agent'),
                    "runtime": "Generic"
                }
            }
        }],
        "schemas": []
    }

    main_pipeline = pipeline["pipelines"][0]
    nodes = []

    # Layout parameters
    x_offset = 100
    y_offset = 100
    x_spacing = 400
    y_spacing = 200

    # Track parallel vs sequential layout
    parallel_group_1 = ["01_regulatory_analysis", "02_pathogenicity_scoring"]

    # Generate nodes for each workflow step
    for idx, step in enumerate(workflow):
        step_id = step['step']
        module_id = step['module']
        module_info = modules.get(module_id, {})

        # Determine node position
        if step_id in parallel_group_1:
            # Parallel nodes side by side
            if step_id == "01_regulatory_analysis":
                x_pos = x_offset
                y_pos = y_offset
            else:  # 02_pathogenicity_scoring
                x_pos = x_offset + x_spacing
                y_pos = y_offset
        elif step_id == "03_differential_diagnosis":
            # Center below parallel nodes
            x_pos = x_offset + x_spacing // 2
            y_pos = y_offset + y_spacing
        elif step_id == "04_tool_call_generation":
            x_pos = x_offset + x_spacing // 2
            y_pos = y_offset + y_spacing * 2
        elif step_id == "05_report_generation":
            x_pos = x_offset + x_spacing // 2
            y_pos = y_offset + y_spacing * 3
        else:
            x_pos = x_offset + (idx * x_spacing)
            y_pos = y_offset

        # Get notebook path
        notebook_path = f"{module_info['path']}/{module_info['notebook']}"

        # Create node
        node = {
            "id": str(uuid.uuid4()),
            "type": "execution_node",
            "op": "execute-notebook-node",
            "app_data": {
                "component_parameters": {
                    "dependencies": [],
                    "include_subdirectories": False,
                    "outputs": list(step.get('outputs', {}).values()),
                    "env_vars": [],
                    "kubernetes_pod_annotations": [],
                    "kubernetes_pod_labels": [],
                    "kubernetes_secrets": [],
                    "kubernetes_shared_mem_size": {},
                    "kubernetes_tolerations": [],
                    "mounted_volumes": [],
                    "filename": notebook_path,
                    "runtime_image": "",
                    "cpu": step.get('resources', {}).get('cpu', 2),
                    "cpu_limit": step.get('resources', {}).get('cpu', 2),
                    "memory": step.get('resources', {}).get('memory', '4Gi'),
                    "memory_limit": step.get('resources', {}).get('memory', '4Gi'),
                    "gpu": 0,
                    "gpu_vendor": ""
                },
                "label": step_id,
                "ui_data": {
                    "label": step_id,
                    "image": "/static/elyra/notebook.svg",
                    "x_pos": x_pos,
                    "y_pos": y_pos,
                    "description": step.get('description', '')
                }
            },
            "inputs": [],
            "outputs": []
        }

        # Add dependencies as input links
        for dep_step in step.get('depends_on', []):
            # Find the node id for this dependency
            dep_node = next((n for n in nodes if n['app_data']['label'] == dep_step), None)
            if dep_node:
                node["inputs"].append({
                    "id": str(uuid.uuid4()),
                    "app_data": {
                        "ui_data": {
                            "class_name": "d3-data-link"
                        }
                    },
                    "links": [{
                        "id": str(uuid.uuid4()),
                        "node_id_ref": dep_node["id"],
                        "port_id_ref": "outPort"
                    }]
                })

                # Add output port to dependency node
                if not dep_node.get("outputs"):
                    dep_node["outputs"] = []
                dep_node["outputs"].append({
                    "id": "outPort",
                    "app_data": {
                        "ui_data": {
                            "class_name": "d3-data-port"
                        }
                    }
                })

        nodes.append(node)

    main_pipeline["nodes"] = nodes

    # Write pipeline
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(pipeline, f, indent=2)

    print(f"✓ Generated Elyra pipeline: {output_path}")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Parallel nodes: {len(parallel_group_1)}")
    print(f"  Sequential nodes: {len(nodes) - len(parallel_group_1)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        topology_path = "topology.yaml"
        output_path = "elyra/UH2025Agent.pipeline"
    else:
        topology_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else "elyra/UH2025Agent.pipeline"

    generate_elyra_pipeline(topology_path, output_path)
