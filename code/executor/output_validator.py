"""
Output validator - validates notebook outputs against schemas.

Supports:
- JSON Schema validation
- Custom validation rules
- Type checking
- Range constraints
- Required field checking

Usage:
    validator = OutputValidator()
    errors = validator.validate_json(
        data={"variants": [...]},
        schema_path="schemas/variant_output.json"
    )
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Single validation error."""

    field: str
    message: str
    value: Any = None

    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.field}: {self.message} (got: {self.value})"
        return f"{self.field}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    errors: List[ValidationError]

    def __bool__(self) -> bool:
        return self.valid

    def error_messages(self) -> List[str]:
        return [str(e) for e in self.errors]


class OutputValidator:
    """
    Validates notebook outputs against schemas and rules.

    Provides flexible validation for:
    - JSON Schema validation (if jsonschema available)
    - Built-in type and constraint checking
    - Custom validation functions
    """

    def __init__(
        self,
        schemas_dir: Optional[Path] = None,
        strict: bool = False,
    ):
        """
        Initialize output validator.

        Args:
            schemas_dir: Directory containing JSON schema files
            strict: If True, fail on unknown fields
        """
        self.schemas_dir = Path(schemas_dir) if schemas_dir else None
        self.strict = strict
        self._schemas_cache: Dict[str, Dict] = {}

        # Check for jsonschema library
        try:
            import jsonschema
            self._has_jsonschema = True
        except ImportError:
            self._has_jsonschema = False
            logger.warning(
                "jsonschema not installed. Using built-in validation only. "
                "Install with: pip install jsonschema"
            )

    def load_schema(self, schema_path: Union[str, Path]) -> Dict:
        """
        Load and cache JSON schema.

        Args:
            schema_path: Path to schema file (absolute or relative to schemas_dir)

        Returns:
            Parsed schema dictionary

        Raises:
            FileNotFoundError: If schema file not found
        """
        schema_path = Path(schema_path)

        # Try relative to schemas_dir
        if not schema_path.is_absolute() and self.schemas_dir:
            schema_path = self.schemas_dir / schema_path

        cache_key = str(schema_path)
        if cache_key in self._schemas_cache:
            return self._schemas_cache[cache_key]

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(schema_path) as f:
            schema = json.load(f)

        self._schemas_cache[cache_key] = schema
        return schema

    def validate_json(
        self,
        data: Dict[str, Any],
        schema: Optional[Dict] = None,
        schema_path: Optional[Union[str, Path]] = None,
    ) -> ValidationResult:
        """
        Validate JSON data against schema.

        Args:
            data: Data to validate
            schema: Schema dictionary (inline)
            schema_path: Path to schema file

        Returns:
            ValidationResult with any errors

        Raises:
            ValueError: If neither schema nor schema_path provided
        """
        if schema is None and schema_path is not None:
            schema = self.load_schema(schema_path)

        if schema is None:
            raise ValueError("Must provide either schema or schema_path")

        errors = []

        # Use jsonschema if available
        if self._has_jsonschema:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            for error in validator.iter_errors(data):
                path = '.'.join(str(p) for p in error.absolute_path) or 'root'
                errors.append(ValidationError(
                    field=path,
                    message=error.message,
                    value=error.instance if len(str(error.instance)) < 100 else '...',
                ))
        else:
            # Fallback to built-in validation
            errors.extend(self._validate_builtin(data, schema, path=''))

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def _validate_builtin(
        self,
        data: Any,
        schema: Dict,
        path: str,
    ) -> List[ValidationError]:
        """
        Built-in validation without jsonschema library.

        Args:
            data: Data to validate
            schema: Schema definition
            path: Current path in data structure

        Returns:
            List of validation errors
        """
        errors = []

        # Type checking
        schema_type = schema.get('type')
        if schema_type:
            type_map = {
                'object': dict,
                'array': list,
                'string': str,
                'integer': int,
                'number': (int, float),
                'boolean': bool,
                'null': type(None),
            }

            expected_type = type_map.get(schema_type)
            if expected_type and not isinstance(data, expected_type):
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"Expected type '{schema_type}'",
                    value=type(data).__name__,
                ))
                return errors  # Stop validation on type mismatch

        # Object validation
        if schema_type == 'object' and isinstance(data, dict):
            # Required fields
            for field in schema.get('required', []):
                if field not in data:
                    errors.append(ValidationError(
                        field=f"{path}.{field}" if path else field,
                        message="Required field missing",
                    ))

            # Property validation
            properties = schema.get('properties', {})
            for key, value in data.items():
                field_path = f"{path}.{key}" if path else key

                if key in properties:
                    errors.extend(self._validate_builtin(
                        value,
                        properties[key],
                        field_path,
                    ))
                elif self.strict and 'additionalProperties' not in schema:
                    errors.append(ValidationError(
                        field=field_path,
                        message="Unknown field (strict mode)",
                    ))

        # Array validation
        if schema_type == 'array' and isinstance(data, list):
            items_schema = schema.get('items')
            if items_schema:
                for i, item in enumerate(data):
                    errors.extend(self._validate_builtin(
                        item,
                        items_schema,
                        f"{path}[{i}]",
                    ))

            # Min/max items
            if 'minItems' in schema and len(data) < schema['minItems']:
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"Array has fewer than {schema['minItems']} items",
                    value=len(data),
                ))
            if 'maxItems' in schema and len(data) > schema['maxItems']:
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"Array has more than {schema['maxItems']} items",
                    value=len(data),
                ))

        # Number constraints
        if schema_type in ('integer', 'number') and isinstance(data, (int, float)):
            if 'minimum' in schema and data < schema['minimum']:
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"Value below minimum ({schema['minimum']})",
                    value=data,
                ))
            if 'maximum' in schema and data > schema['maximum']:
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"Value above maximum ({schema['maximum']})",
                    value=data,
                ))

        # String constraints
        if schema_type == 'string' and isinstance(data, str):
            if 'minLength' in schema and len(data) < schema['minLength']:
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"String shorter than {schema['minLength']} chars",
                    value=len(data),
                ))
            if 'maxLength' in schema and len(data) > schema['maxLength']:
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"String longer than {schema['maxLength']} chars",
                    value=len(data),
                ))
            if 'enum' in schema and data not in schema['enum']:
                errors.append(ValidationError(
                    field=path or 'root',
                    message=f"Value not in enum: {schema['enum']}",
                    value=data,
                ))
            if 'pattern' in schema:
                import re
                if not re.match(schema['pattern'], data):
                    errors.append(ValidationError(
                        field=path or 'root',
                        message=f"Value doesn't match pattern: {schema['pattern']}",
                        value=data,
                    ))

        return errors

    def validate_file(
        self,
        file_path: Union[str, Path],
        schema: Optional[Dict] = None,
        schema_path: Optional[Union[str, Path]] = None,
    ) -> ValidationResult:
        """
        Validate JSON file against schema.

        Args:
            file_path: Path to JSON file
            schema: Schema dictionary (inline)
            schema_path: Path to schema file

        Returns:
            ValidationResult
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    field='file',
                    message=f"File not found: {file_path}",
                )],
            )

        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    field='json',
                    message=f"Invalid JSON: {e}",
                )],
            )

        return self.validate_json(data, schema=schema, schema_path=schema_path)

    def validate_outputs(
        self,
        output_dir: Path,
        output_schemas: Dict[str, Union[str, Dict]],
    ) -> Dict[str, ValidationResult]:
        """
        Validate multiple output files in a directory.

        Args:
            output_dir: Directory containing output files
            output_schemas: Mapping of filename -> schema or schema_path

        Returns:
            Dictionary of filename -> ValidationResult
        """
        results = {}
        output_dir = Path(output_dir)

        for filename, schema_spec in output_schemas.items():
            file_path = output_dir / filename

            # Determine schema
            if isinstance(schema_spec, dict):
                schema = schema_spec
                schema_path = None
            else:
                schema = None
                schema_path = schema_spec

            results[filename] = self.validate_file(
                file_path,
                schema=schema,
                schema_path=schema_path,
            )

        return results


# Pre-defined schemas for common module outputs
COMMON_SCHEMAS = {
    'variant_output': {
        'type': 'object',
        'required': ['variants'],
        'properties': {
            'variants': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['chrom', 'pos', 'ref', 'alt'],
                    'properties': {
                        'chrom': {'type': 'string'},
                        'pos': {'type': 'integer', 'minimum': 1},
                        'ref': {'type': 'string', 'minLength': 1},
                        'alt': {'type': 'string', 'minLength': 1},
                    },
                },
            },
            'metadata': {'type': 'object'},
        },
    },

    'pathogenicity_output': {
        'type': 'object',
        'required': ['predictions'],
        'properties': {
            'predictions': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['variant_id', 'score'],
                    'properties': {
                        'variant_id': {'type': 'string'},
                        'score': {'type': 'number', 'minimum': 0, 'maximum': 1},
                        'classification': {
                            'type': 'string',
                            'enum': ['pathogenic', 'likely_pathogenic', 'uncertain', 'likely_benign', 'benign'],
                        },
                    },
                },
            },
        },
    },

    'analysis_summary': {
        'type': 'object',
        'required': ['summary'],
        'properties': {
            'summary': {
                'type': 'object',
                'properties': {
                    'total_variants': {'type': 'integer', 'minimum': 0},
                    'pathogenic_count': {'type': 'integer', 'minimum': 0},
                    'benign_count': {'type': 'integer', 'minimum': 0},
                },
            },
            'top_findings': {'type': 'array'},
            'recommendations': {'type': 'array'},
        },
    },
}


def validate_with_schema(
    data: Dict[str, Any],
    schema_name: str,
) -> ValidationResult:
    """
    Convenience function to validate with a common schema.

    Args:
        data: Data to validate
        schema_name: Name of common schema

    Returns:
        ValidationResult
    """
    if schema_name not in COMMON_SCHEMAS:
        return ValidationResult(
            valid=False,
            errors=[ValidationError(
                field='schema',
                message=f"Unknown schema: {schema_name}. Available: {list(COMMON_SCHEMAS.keys())}",
            )],
        )

    validator = OutputValidator()
    return validator.validate_json(data, schema=COMMON_SCHEMAS[schema_name])


def main():
    """CLI for testing validation."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate JSON output files')
    parser.add_argument('file', help='JSON file to validate')
    parser.add_argument('--schema', help='Path to JSON schema file')
    parser.add_argument('--common-schema', choices=list(COMMON_SCHEMAS.keys()),
                        help='Use a common schema')
    parser.add_argument('--strict', action='store_true',
                        help='Fail on unknown fields')

    args = parser.parse_args()

    validator = OutputValidator(strict=args.strict)

    # Determine schema
    if args.common_schema:
        schema = COMMON_SCHEMAS[args.common_schema]
        schema_path = None
    elif args.schema:
        schema = None
        schema_path = args.schema
    else:
        print("Error: Must provide --schema or --common-schema")
        return 1

    # Validate
    result = validator.validate_file(
        args.file,
        schema=schema,
        schema_path=schema_path,
    )

    # Print results
    print("\n" + "=" * 60)
    print("VALIDATION RESULT")
    print("=" * 60)

    if result.valid:
        print("✓ Valid")
        return 0
    else:
        print("✗ Invalid")
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
