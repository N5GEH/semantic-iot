from pathlib import Path
from semantic_iot import RDFGenerator, APIPostprocessor

# Path to HTTP ontology and OpenAPI spec (adjust as needed)
HTTP_ONTO = Path(__file__).parent.parent / f'examples/fiware/ontologies/Http.ttl'
SWAGGER   = Path(__file__).parent / f'openhab_swagger_spec.yaml'


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    kg = project_root / f'test/openhab_kg.ttl'

    out_ext = project_root / f'test/results/openhab_swagger_extended.ttl'

    postprocessor = APIPostprocessor(
        kg_path=kg,
        api_spec_path=SWAGGER,
        http_onto=HTTP_ONTO
    )
    postprocessor.extend_kg()
    postprocessor.kg.serialize(destination=str(out_ext), format='turtle')

