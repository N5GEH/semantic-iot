from pathlib import Path
from semantic_iot import RDFGenerator, APIPostprocessor

# Path to HTTP ontology and OpenAPI spec (adjust as needed)
HTTP_ONTO = Path(__file__).parent.parent / f'examples/fiware/ontologies/Http.ttl'
OPENAPI   = Path(__file__).parent.parent / f'examples/fiware/kgcp/api_spec.json'


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    mapping_file = project_root / f'examples/fiware/kgcp/rml/fiware_hotel_rml.ttl'
    config_file  = project_root / f'examples/fiware/kgcp/fiware_config.json'
    metrics = dict()

    rdf_gen = RDFGenerator(
        mapping_file=str(mapping_file),
        platform_config=str(config_file)
    )

    for hotel in (
            'fiware_entities_2rooms',
            'fiware_entities_10rooms',
            'fiware_entities_50rooms',
            'fiware_entities_100rooms',
            'fiware_entities_500rooms',
            'fiware_entities_1000rooms'
    ):
        src = project_root / f'examples/fiware/hotel_dataset/{hotel}.json'
        dst = project_root / f'test/results/{hotel}.ttl'

        # Always also extend with HTTP metadata
        # Generate extension regardless of measure_metrics setting
        # First ensure base TTL exists (either from metric run or direct generate)
        if not dst.exists():
            rdf_gen.generate_rdf(
                source_file=str(src),
                destination_file=str(dst),
                engine='morph-kgc'
            )
        out_ext = project_root / f'test/results/{hotel}_extended.ttl'

        postprocessor = APIPostprocessor(
            kg_path=dst,
            api_spec_path=OPENAPI,
            http_onto=HTTP_ONTO
        )
        postprocessor.extend_kg()
        postprocessor.kg.serialize(destination=str(out_ext), format='turtle')

