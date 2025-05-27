import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from semantic_iot.RDF_generator import RDFGenerator

# # Test with fiware_hotel_rml.ttl
# print("Testing fiware_hotel_rml.ttl...")
# generator1 = RDFGenerator(
#     mapping_file=r"c:\Users\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\examples\fiware\kgcp\rml\brick\fiware_hotel_rml.ttl"
# )
# try:
#     generator1.generate_rdf(
#         source_file=r"c:\Users\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\examples\fiware\hotel_dataset\fiware_entities_2rooms.json",
#         destination_file="test_output1.ttl"
#     )
#     print("✓ First mapping file generated output successfully")
# except Exception as e:
#     print(f"✗ First mapping file failed: {e}")

# Test with fiware_hotel_rml_two.ttl
print("\nTesting fiware_hotel_rml_two.ttl...")
generator2 = RDFGenerator(
    mapping_file=r"c:\Users\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\LLM_models\datasets\fiware_v1_hotel\results\fiware_hotel_rml_two.ttl"
)
try:
    generator2.generate_rdf(
        source_file=r"c:\Users\56xsl\Obsidian\Compass\Projects\Bachelorarbeit\Code\semantic-iot\examples\fiware\hotel_dataset\fiware_entities_2rooms.json",
        destination_file="test_output2.ttl"
    )
    print("✓ Second mapping file generated output successfully")
except Exception as e:
    print(f"✗ Second mapping file failed: {e}")

# Check file sizes to see if anything was generated
try:
    size1 = os.path.getsize("test_output1.ttl")
    print(f"Output file 1 size: {size1} bytes")
except:
    print("Output file 1 not found")

try:
    size2 = os.path.getsize("test_output2.ttl")
    print(f"Output file 2 size: {size2} bytes")
except:
    print("Output file 2 not found")
