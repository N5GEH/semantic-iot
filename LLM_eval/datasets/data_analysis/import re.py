import re
from collections import defaultdict

# Raw data strings
bloom_verb_1 = "bloom_verbfrequencydefine5list2identify2memorize1identify10examine1identify1recall9memorize10operate26identify5develop3relate1demonstrate3use6locate1compose1recall1use3identify3develop3relate2demonstrate4locate1compose1use9translate1recall1use8relate1develop1use3identify3demonstrate1use2identify3develop2relate2demonstrate3locate1compose1use6translate1recall1use5relate1develop1use2identify3demonstrate1use1identify3develop3relate2demonstrate4locate1compose1use9translate1recall1use8relate1develop1use3identify3demonstrate1use2identify3develop3relate2demonstrate4locate1compose1use9translate1recall1use8relate1develop1use3identify3demonstrate1use2identify3develop3relate2demonstrate4locate1compose1use9translate1recall1use8relate1develop1use3identify3demonstrate1use2identify3develop2relate2demonstrate3use4translate1recall1use5relate1develop1use3locate1compose1identify3demonstrate1use1create1relate1compose1create1create2demonstrate2child relationship2use3compose1use4create2demonstrate1use8combine1identify3develop2relate2demonstrate3use4translate1recall1use5relate1develop1use3locate1compose1identify3demonstrate1use1create1relate1compose1create1create2demonstrate2child relationship2use3compose1use4create2demonstrate1use8combine1identify3develop2relate2demonstrate3use4translate1recall1use5relate1develop1use3locate1compose1identify3demonstrate1use1create1relate1compose1create1create2demonstrate2child relationship2use3compose1use4create2demonstrate1use8combine1organize1compose1use1"
dataset1 = """

"""

bloom_verb_2 = "bloom_verbfrequencyuse2list3define4implement1name14use5create1add2organize4structure1demonstrate2identify1use3demonstrate1use1create1implement2use16create1add4organize4structure3demonstrate2demonstrate1use1create1implement4use10create1add3organize2structure2demonstrate2demonstrate1use1create1use3organize2implement3use13create1add4organize2structure3demonstrate2demonstrate1use1create1use2organize2implement4use11create1add4organize4structure3demonstrate2compose1demonstrate1use1create1implement4use11create1add4organize4structure3demonstrate2compose1demonstrate1use1create1implement4use8create1add3organize4structure2demonstrate2use2demonstrate1create1implement3use8create1add3organize4structure2demonstrate2use2demonstrate1create1implement3use8create1add3organize4structure2demonstrate2use2demonstrate1create1implement3use7compose1demonstrate1use1create1create1add4use6organize4structure3demonstrate2implement4use3compose1demonstrate1use1create1create1add4use6organize4structure3demonstrate2implement4use11create1add4organize4structure3demonstrate2compose1demonstrate1use1create1implement4compose1assess1complete1validate2assemble1add1compose1compose1compose1compose1compose1compose1compose1compose1compose1compose1compose1compose1"
dataset2 = """
"""

bloom_verb_3 = "bloom_verbfrequencydevelop2recall2use6use2identify1use6develop1identify1create1use3recall2demonstrate2develop1recall1use3use2identify1use8develop2recall1identify1create1use2recall2demonstrate2develop2recall2use6use2identify1use6develop1identify1create1use3recall2demonstrate2create1compose5organize1compose2record1identify5recognize1identify2identify2list1identify14use12define1recall12name6record9recall13use26identify6recall2use4identify4use2recall1recall3use6use1identify3use6examine1demonstrate1recall1identify2use3use1recall2use6identify1use1identify2use2recall2identify1demonstrate1use2recall2use9identify1use1demonstrate1identify2use3recall2use4recall2use9identify1use1demonstrate1identify2use3recall2use4recall2use9identify1use1demonstrate1identify1use6recall2recall5use6identify1use2demonstrate1use2recall5use6identify1use2demonstrate1use2recall5use6identify1use2demonstrate1use2assemble2compose4develop3produce1use1"
dataset3 = """
identify	15
examine	10
compare	9
relate	8
organize	5
compose	4
list	3
create	3
extract	3
design	2
categorize	2
investigate	2
explain	1
classify	1
"""
def parse_verb_frequencies(data_string):
    """Parse verb frequency data from a string."""
    # Remove the prefix 'bloom_verbfrequency'
    data = data_string.replace('bloom_verbfrequency', '')
    
    # Use regex to find verb-frequency pairs
    # This pattern looks for word followed by digits
    pattern = r'([a-zA-Z\s]+?)(\d+)'
    matches = re.findall(pattern, data)
    
    verb_counts = defaultdict(int)
    
    for verb, count in matches:
        # Clean up the verb (remove extra spaces, convert to lowercase)
        verb = verb.strip().lower()
        
        # Skip empty verbs or invalid entries
        if verb and verb != 'child relationship':  # Handle special case
            verb_counts[verb] += int(count)
        elif verb == 'child relationship':
            verb_counts['child_relationship'] += int(count)
    
    return dict(verb_counts)

def sort_frequencies(verb_dict):
    """Sort verbs by frequency (descending) then alphabetically."""
    return sorted(verb_dict.items(), key=lambda x: (-x[1], x[0]))

# Parse all three datasets
print("Parsing datasets...")
freq1 = parse_verb_frequencies(dataset1)
freq2 = parse_verb_frequencies(dataset2)
freq3 = parse_verb_frequencies(dataset3)

print("\n" + "="*50)
print("DATASET 1 - Verb Frequencies (sorted by frequency)")
print("="*50)
sorted_freq1 = sort_frequencies(freq1)
for verb, count in sorted_freq1:
    print(f"{verb}: {count}")

print("\n" + "="*50)
print("DATASET 2 - Verb Frequencies (sorted by frequency)")
print("="*50)
sorted_freq2 = sort_frequencies(freq2)
for verb, count in sorted_freq2:
    print(f"{verb}: {count}")

print("\n" + "="*50)
print("DATASET 3 - Verb Frequencies (sorted by frequency)")
print("="*50)
sorted_freq3 = sort_frequencies(freq3)
for verb, count in sorted_freq3:
    print(f"{verb}: {count}")

# Summary statistics
print("\n" + "="*50)
print("SUMMARY STATISTICS")
print("="*50)
print(f"Dataset 1: {len(freq1)} unique verbs, {sum(freq1.values())} total occurrences")
print(f"Dataset 2: {len(freq2)} unique verbs, {sum(freq2.values())} total occurrences")
print(f"Dataset 3: {len(freq3)} unique verbs, {sum(freq3.values())} total occurrences")

# Find common verbs across all datasets
common_verbs = set(freq1.keys()) & set(freq2.keys()) & set(freq3.keys())
print(f"\nCommon verbs across all datasets: {len(common_verbs)}")
if common_verbs:
    print("Common verbs:", sorted(common_verbs))