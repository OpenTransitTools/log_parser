"""
  Will parse mod_security log files
  This is needed for OpenTripPlanner (OTP) v2.x, which uses HTTP POST (graphql) requests,
  and with Apache, the mod_security2 modules is how you see these requests
"""

import os
import re
from ott.utils.parse.cmdline.base_cmdline import file_cmdline


def parse_modsec_audit_log(filename):
    """
    written by Claude (github) in Aug 2025 (with a couple hacks by Frank)

    seemingly great job (almost) at reading the A-Z blocks for each unique session 
    opens a mod_security2 log file, and returns a list of dicts, where each dict
    is the unique request, broken up by sections.  
    
    For this project, we're mostly interested in section 'C', which contains the 
    graphql POST payload input into OTP.  We also want other sections, like the
    referrer and device used, etc...
    """
    entries = []
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # hack: add some junk before content, b/c if no junk the first record will get culled via the 'next()' 
    content = "\n\n" + content

    # Split into entries by boundary lines like '---abc123-A---'
    raw_entries = re.split(r"\n--([a-fA-F0-9]+)-A--\n", content)
    it = iter(raw_entries)  # via split, return a list: [before junk, id1, entry1, id2, entry2, ...]
    next(it)  # skip junk before the first entry
    for unique_id, entry in zip(it, it):
        entry_dict = {"id": unique_id}
        # hack: add back the A section header culled out when split'ing content to obtain id above
        entry = "\n--{}-A--\n{}".format(unique_id, entry)
        #import pdb; pdb.set_trace()
        # Section parsing: ---abc123-A---, ---abc123-B---, ---abc123-C---, etc.
        sections = re.split(rf"\n--{unique_id}-([A-Z])--\n", entry)
        # [before, section_letter1, section1, section_letter2, section2, ...]
        section_it = iter(sections)
        next(section_it)  # skip content before first section
        for section_letter, section_content in zip(section_it, section_it):
            entry_dict[section_letter] = section_content.strip()
        entries.append(entry_dict)
    return entries


def parse_section_a(req):
    """
    --9e7b8111-A--
    [10/Aug/2025:15:39:41 --0700] xxx 172.25.90.86 55986 172.25.102.224 443
    """
    date = None
    ip = None
    sec_a = req.get("A", None)

    try:
        date_match = re.search(r"\[(.*?)\]", sec_a)
        date = date_match.group(1) if date_match else None
        date = date # convert to date time
    except Exception as e:
        pass

    try:
        ip_matches = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", sec_a)
        ip = ip_matches[0]
    except Exception as e:
        pass
    return date, ip


def parse_section_b(req):
    """
    section b has request headers
    POST /rtp/gtfs/v1 HTTP/1.1
    Referer: https://labs-5.trimet.org/
    User-Agent: Mozilla/5.0 (Win...
    """
    user_agent = ""    
    referer = ""
    url = ""

    sec_b = req.get("B", None)
    try:    
        #import pdb; pdb.set_trace()
        ua = re.search(r"User-Agent: (.*)\n", sec_b)
        user_agent = ua.group(1) if ua else ""
    except Exception as e:
        pass

    try:    
        r = re.search(r"Referer: (.*)\n", sec_b)
        referer = r.group(1) if r else ""
    except Exception as e:
        pass

    try:    
        u = re.search(r"POST (.*) HTTP.*\n", sec_b)
        url = u.group(1) if u else ""
    except Exception as e:
        pass


    return user_agent, url, referer


def parse_section_c(req):
    """
    section c has the POST payload
    split the string at variables, and return that json of key/value pairs

    --9e7b8111-C--
    ....description\ninputField\n}\n}\n}\n","variables":{"date":"2025-08-10","time":"15:23",...
    """
    ret_val = None

    sec_c = req.get("C", None)
    try:
        if "query" in sec_c:
            if "variables" in sec_c:
                vars = sec_c.split("variables\":")
                ret_val = vars[1][:-1]  # return things right of the variables, except for dangling bracket
            else:
                ret_val = sec_c
    except Exception as e:
        pass
    return ret_val


def parse_section_f(req, def_code="520"):
    """
    section f has response headers
    pull out the HTTP status code
    
    --ac12e444-F--
    HTTP/1.1 200 OK
    Content-Encoding: gzip    
    """
    code = def_code
    
    sec_f = req.get("F", None)
    try:
        c = re.search(r"HTTP.*(\d{3}).*", sec_f)
        code = c.group(1) if c else def_code
    except Exception as e:
        pass
    return code


def parse_raw_request(req):
    """
    parse out the various 'raw' elements from a given mod_security2 log record (dict)
    parser.py attribute names: '{ip} - - [{apache_dt}] "{meth} {url} {http}" {code} {size} "{referer}" "{browser}"\n'
    """
    rec = {}

    date, ip = parse_section_a(req)
    rec['ip'] = ip
    rec['apache_dt'] = date

    user_agent, url, referer = parse_section_b(req)
    rec['browser'] = user_agent
    rec['url'] = url
    rec['referer'] = referer

    payload = parse_section_c(req)
    rec['payload'] = payload

    code = parse_section_f(req)
    rec['code'] = code

    return rec


def parse_processed(req):
    """
    parse out the 'ul' elements from a given raw mod_security2 record
    """
    rec = {}
    rec['ip'] = ""
    rec['date'] = ""
    rec['url'] = ""
    rec['code'] = ""
    rec['referrer'] = ""
    rec['browser'] = ""


def parse_log_file(file: os.PathLike):
    ret_val = []
    parsed_entries = parse_modsec_audit_log(file)
    for e in parsed_entries:
        rec = parse_raw_request(e)
        if rec and rec.get('url', None):
            url = rec.get('url', "")
            if 'atisExe' not in url and 'solr/select' not in url:
                ret_val.append(rec)
    return ret_val


def simple_test(parse=True):
    cmd = file_cmdline("bin/parser_modsec_test", "docs/modsec_audit.txt")
    parsed_entries = parse_modsec_audit_log(cmd.file)
    for e in parsed_entries:
        if parse:
            raw = parse_raw_request(e)
            print(raw)
            pro = parse_processed(raw)
        else:
            print(f"ID: {e['id']}")
            print("Sections:", list(e.keys()))
            for k in list(e.keys()):
                print(e.get(k, 'No section {}'.format(k)))
                print()
                #break
            print("=" * 60)
            print()
        
