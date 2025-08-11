"""
  Will parse mod_security log files
  This is needed for OpenTripPlanner (OTP) v2.x, which uses HTTP POST (graphql) requests,
  and with Apache, the mod_security2 modules is how you see these requests
"""

import re

def parse_modsec_audit_log(filename):
    """
    written by Claude in Aug 2025 (github)

    seemingly great job at reading the A-Z blocks for each unique session 
    opens a mod_security2 log file, and returns a list of dicts, where each dict
    is the unique request, broken up by sections.  
    
    For this project, we're mostly interested in section 'C', which contains the 
    graphql POST payload input into OTP.  We also want other sections, like the
    referrer and device used, etc...
    """
    entries = []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Split into entries by boundary lines like '---abc123-A---'
    raw_entries = re.split(r"\n--([a-fA-F0-9]+)-A--\n", content)
    # re.split returns a list: [before, id1, entry1, id2, entry2, ...]
    it = iter(raw_entries)
    next(it)  # skip content before the first entry
    for unique_id, entry in zip(it, it):
        entry_dict = {"id": unique_id}
        # Section parsing: ---abc123-B---, ---abc123-C---, etc.
        sections = re.split(rf"\n--{unique_id}-([A-Z])--\n", entry)
        # [before, section_letter1, section1, section_letter2, section2, ...]
        section_it = iter(sections)
        next(section_it)  # skip content before first section
        for section_letter, section_content in zip(section_it, section_it):
            entry_dict[section_letter] = section_content.strip()
        entries.append(entry_dict)
    return entries


def parse_request(rec):
    """
    parse out the various elements from a given mod_security2 log record (dict)
    """
    #import pdb; pdb.set_trace()
    print(f"ID: {rec['id']}")
    print(rec)

def simple_test(parse=True):
    parsed_entries = parse_modsec_audit_log('docs/modsec_audit.txt')
    for e in parsed_entries:
        if parse:
            parse_request(e)
        else:
            print(f"ID: {e['id']}")
            print("Sections:", list(e.keys()))
            #print(e.get('C', 'No POST payload'))
            print(e.get('H', 'No H section'))
            print("=" * 60)
        
