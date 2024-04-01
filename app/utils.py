import re


def safe_get(d, keys, default=""):
    """
    Attempt to get a value from a nested dictionary (d) using a list of keys.
    Returns the value if found, else returns default (an empty string).
    """
    try:
        for key in keys:
            if isinstance(d, dict):
                d = d.get(key, default)
            elif isinstance(d, list):
                d = d[int(key)] if len(d) > int(key) else default
            else:
                return default
    except (TypeError, ValueError, AttributeError, IndexError):
        return default
    return d if isinstance(d, str) else str(d)


def extract_from_json(clinical_study):
    # 0. Subset JSON
    extracted_json = {}

    # 1. PROTOCOL SECTION
    protocol_section = clinical_study.get("protocolSection", {})

    # 1.1. IDENTIFICATION MODULE
    identification_module = protocol_section.get("identificationModule", {})
    extracted_json.update({
        "National Clinical Identification NCT ID": safe_get(identification_module, ["nctId"]),
        "Organization study identification": safe_get(identification_module, ["orgStudyIdInfo", "id"]),
        "EudraCT number": safe_get(identification_module, ["secondaryIdInfos", 0, "id"], ""),
        "Organization": safe_get(identification_module, ["organization", "fullName"]),
        "Organization class": safe_get(identification_module, ["organization", "class"]),
        "Brief title": safe_get(identification_module, ["briefTitle"]),
        "Official title": safe_get(identification_module, ["officialTitle"]),
    })

    # 1.2. STATUS MODULE
    status_module = protocol_section.get("statusModule", {})
    extracted_json.update({
        "Overall status": safe_get(status_module, ["overallStatus"]),
        "Start date": safe_get(status_module, ["startDateStruct", "date"]),
        "Primary completion date": safe_get(status_module, ["primaryCompletionDateStruct", "date"]),
        "Completion date": safe_get(status_module, ["completionDateStruct", "date"]),
        "Verification date": safe_get(status_module, ["statusVerifiedDate"]),
        "Study first submitted date": safe_get(status_module, ["studyFirstSubmitDate"]),
        "Results first submitted date": safe_get(status_module, ["resultsFirstSubmitDate"]),
        "Last update submitted date": safe_get(status_module, ["lastUpdateSubmitDate"]),
        "Last update posted date": safe_get(status_module, ["lastUpdatePostDateStruct", "date"]),
    })

    # 1.3. SPONSOR/COLLABORATORS MODULE
    sponsor_collaborators_module = protocol_section.get("sponsorCollaboratorsModule", {})
    extracted_json.update({
        "Lead sponsor": safe_get(sponsor_collaborators_module, ["leadSponsor", "name"]),
        "Lead sponsor class": safe_get(sponsor_collaborators_module, ["leadSponsor", "class"]),
    })

    # 1.4. DESCRIPTION MODULE
    description_module = protocol_section.get("descriptionModule", {})
    extracted_json.update({
        "Brief summary": safe_get(description_module, ["briefSummary"]),
        "Detailed description": safe_get(description_module, ["detailedDescription"]),
    })

    # 1.5. CONDITIONS MODULE
    conditions_module = protocol_section.get("conditionsModule", {})
    extracted_json.update({
        "Condition": safe_get(conditions_module, ["conditions"]),
        "Conditions keywords": safe_get(conditions_module, ["keywords"]),
    })

    # 1.6. DESIGN MODULE
    design_module = protocol_section.get("designModule", {})
    extracted_json.update({
        "Study type": safe_get(design_module, ["studyType"]),
        "Phases": safe_get(design_module, ["phases"]),
        "Allocation": safe_get(design_module, ["designInfo", "allocation"]),
        "Intervention model": safe_get(design_module, ["designInfo", "interventionModel"]),
        "Primary purpose": safe_get(design_module, ["designInfo", "primaryPurpose"]),
        "Masking": safe_get(design_module, ["designInfo", "maskingInfo", "masking"]),
        "Who is masked": safe_get(design_module, ["designInfo", "maskingInfo", "whoMasked"]),
        "Enrollment count": safe_get(design_module, ["enrollmentInfo", "count"]),
        "Enrollment type": safe_get(design_module, ["enrollmentInfo", "type"]),
    })

    # 1.7. ARMS INTERVENTIONS MODULE
    arms_interventions_module = protocol_section.get("armsInterventionsModule", {})
    extracted_json.update({
        "Arms group 0 label": safe_get(arms_interventions_module, ["armGroups", 0, "label"], ""),
        "Arms group 0 type": safe_get(arms_interventions_module, ["armGroups", 0, "type"], ""),
        "Arms group 0 description": safe_get(arms_interventions_module, ["armGroups", 0, "description"], ""),
        "Arms group 0 intervention names": safe_get(arms_interventions_module, ["armGroups", 0, "interventionNames"],
                                                    ""),
        "Arms group 1 label": safe_get(arms_interventions_module, ["armGroups", 1, "label"], ""),
        "Arms group 1 type": safe_get(arms_interventions_module, ["armGroups", 1, "type"], ""),
        "Arms group 1 description": safe_get(arms_interventions_module, ["armGroups", 1, "description"], ""),
        "Arms group 1 intervention names": safe_get(arms_interventions_module, ["armGroups", 1, "interventionNames"],
                                                    ""),
        "Arms group 0 intervention type": safe_get(arms_interventions_module, ["interventions", 0, "type"], ""),
        "Arms group 0 intervention name": safe_get(arms_interventions_module, ["interventions", 0, "name"], ""),
        "Arms group 0 intervention description": safe_get(arms_interventions_module,
                                                          ["interventions", 0, "description"], ""),
        "Arms group 0 intervention labels": safe_get(arms_interventions_module, ["interventions", 0, "armGroupLabels"],
                                                     ""),
        "Arms group 1 intervention type": safe_get(arms_interventions_module, ["interventions", 1, "type"], ""),
        "Arms group 1 intervention name": safe_get(arms_interventions_module, ["interventions", 1, "name"], ""),
        "Arms group 1 intervention description": safe_get(arms_interventions_module,
                                                          ["interventions", 1, "description"], ""),
        "Arms group 1 intervention labels": safe_get(arms_interventions_module, ["interventions", 1, "armGroupLabels"],
                                                     ""),
    })

    # 1.8. OUTCOMES MODULE
    outcomes_module = clinical_study.get("protocolSection", {}).get("outcomesModule", {})
    extracted_json.update({
        "Primary outcome": safe_get(outcomes_module, ["primaryOutcomes", 0, "measure"]),
        "Primary outcome description": safe_get(outcomes_module, ["primaryOutcomes", 0, "description"]),
        "Primary outcome time frame": safe_get(outcomes_module, ["primaryOutcomes", 0, "timeFrame"]),
    })

    # 1.9. ELIGIBILITY MODULE
    eligibility_module = protocol_section.get("eligibilityModule", {})
    extracted_json.update({
        "Eligibility criteria": safe_get(eligibility_module, ["eligibilityCriteria"]),
        "Eligibility of healthy volunteer": safe_get(eligibility_module, ["healthyVolunteers"]),
        "Eligibility sex": safe_get(eligibility_module, ["sex"]),
        "Eligibility minimum age": safe_get(eligibility_module, ["minimumAge"]),
        "Eligibility standard age": safe_get(eligibility_module, ["stdAges"]),
    })

    # 2. RESULTS SECTION
    results_section = clinical_study.get("resultsSection", {})
    extracted_json.update({
        "Pre-assignment details": safe_get(results_section, ["participantFlowModule", "preAssignmentDetails"]),
        "Recruitment details": safe_get(results_section, ["participantFlowModule", "recruitmentDetails"]),
        "Recruitment group 0 id": safe_get(results_section, ["participantFlowModule", "groups", 0, "id"], ""),
        "Recruitment group 0 title": safe_get(results_section, ["participantFlowModule", "groups", 0, "title"], ""),
        "Recruitment group 0 description": safe_get(results_section,
                                                    ["participantFlowModule", "groups", 0, "description"], ""),
        "Recruitment group 1 id": safe_get(results_section, ["participantFlowModule", "groups", 1, "id"], ""),
        "Recruitment group 1 title": safe_get(results_section, ["participantFlowModule", "groups", 1, "title"], ""),
        "Recruitment group 1 description": safe_get(results_section,
                                                    ["participantFlowModule", "groups", 1, "description"], ""),
    })

    # 2.1. OUTCOMES MEASURES MODULE
    extracted_json.update({
        "Group IDs": safe_get(results_section, ["outcomeMeasuresModule", "outcomeMeasures", 0, "analyses"]),
        "p-value": safe_get(results_section, ["outcomeMeasuresModule", "outcomeMeasures", 0, "analyses", 0, "pValue"]),
        "Statistical Method": safe_get(results_section, ["outcomeMeasuresModule", "outcomeMeasures", 0, "analyses", 0,
                                                         "statisticalMethod"]),
    })

    # 2.2. MORE INFO MODULE
    more_info_module = results_section.get("moreInfoModule", {})
    extracted_json.update({
        "Limitations and caveats": safe_get(more_info_module, ["limitationsAndCaveats", "description"], ""),
    })

    # 3 HAS RESULTS SECTION
    has_results_section = clinical_study.get("hasResults", {})
    extracted_json.update({
        "Has results": safe_get(clinical_study, ["hasResults"], ""),
    })

    return extracted_json


def flatten_dict(data, parent_key='', sep=' '):
    """
    Flattens a nested dictionary, including dictionaries nested within lists,
    into a flat dictionary with concatenated keys.

    Args:
        data: The nested dictionary to flatten.
        parent_key: The base key to use for the current level of recursion (default '').
        sep: The separator between parent and child keys (default ' ').

    Returns:
        A flat dictionary with concatenated keys representing the structure of the nested input.
    """
    items = []
    if isinstance(data, list):
        # Handle lists by merging them into their parent key without indexing
        for i, element in enumerate(data):
            new_key = f"{parent_key}{sep if parent_key else ''}{i}"
            items.extend(flatten_dict(element, new_key, sep=sep).items())
    elif isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, (dict, list)):
                items.extend(flatten_dict(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
    else:
        items.append((parent_key, data))

    return dict(items)


def replace_double_newline(text):
    """Replaces all occurrences of two or more \n with a single \n, 
    including when preceded or followed by other characters."""
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.replace(";", "&")
    return text


def format_flattened_dict(flat_dict):
    """
    Formats a flattened dictionary into a string representation where each key-value pair is on its own line.

    Args:
        flat_dict: The flat dictionary to format.

    Returns:
        A string representation of the flat dictionary.
    """
    lines = []
    for key, value in flat_dict.items():
        # For list elements, remove the numerical index from the key
        formatted_key = key.rsplit(' ', 1)[0] if key[-1].isdigit() else key
        line = f'"{formatted_key}": "{value}"' if isinstance(value, str) else f'"{formatted_key}": {value}'
        line = replace_double_newline(line)
        lines.append(line)
    return ",\n".join(lines)


pfizer_ncts = [
    "NCT00036270",
    "NCT00038467",
    "NCT00065468",
    "NCT00075218",
    "NCT00083889",
    "NCT00101686",
    "NCT00117598",
    "NCT00141219",
    "NCT00141271",
    "NCT00143403",
    "NCT00143455",
    "NCT00150345",
    "NCT00159874",
    "NCT00159913",
    "NCT00163189",
    "NCT00174252",
    "NCT00174382",
    "NCT00205777",
    "NCT00219544",
    "NCT00232141",
    "NCT00232180",
    "NCT00242710",
    "NCT00254566",
    "NCT00257166",
    "NCT00257192",
    "NCT00280059",
    "NCT00280566",
    "NCT00282464",
    "NCT00282984",
    "NCT00285012",
    "NCT00289991",
    "NCT00311311",
    "NCT00312494",
    "NCT00319501",
    "NCT00333866",
    "NCT00364182",
    "NCT00368745",
    "NCT00373113",
    "NCT00373256",
    "NCT00375674",
    "NCT00376168",
    "NCT00384033",
    "NCT00389519",
    "NCT00393939",
    "NCT00394901",
    "NCT00396097",
    "NCT00401245",
    "NCT00402987",
    "NCT00407745",
    "NCT00413010",
    "NCT00415597",
    "NCT00415623",
    "NCT00420992",
    "NCT00425100",
    "NCT00428597",
    "NCT00435409",
    "NCT00442546",
    "NCT00444925",
    "NCT00445770",
    "NCT00457392",
    "NCT00457691",
    "NCT00459706",
    "NCT00468845",
    "NCT00471146",
    "NCT00474786",
    "NCT00482170",
    "NCT00483548",
    "NCT00507026",
    "NCT00524030",
    "NCT00531479",
    "NCT00536484",
    "NCT00537238",
    "NCT00543439",
    "NCT00546637",
    "NCT00549549",
    "NCT00551135",
    "NCT00553475",
    "NCT00562965",
    "NCT00574873",
    "NCT00596830",
    "NCT00611026",
    "NCT00625872",
    "NCT00627523",
    "NCT00631371",
    "NCT00644969",
    "NCT00662558",
    "NCT00667810",
    "NCT00673049",
    "NCT00676143",
    "NCT00676650",
    "NCT00678392",
    "NCT00683800",
    "NCT00699374",
    "NCT00716859",
    "NCT00733902",
    "NCT00744471",
    "NCT00762463",
    "NCT00795639",
    "NCT00796666",
    "NCT00798707",
    "NCT00806026",
    "NCT00808132",
    "NCT00809354",
    "NCT00814307",
    "NCT00830063",
    "NCT00830167",
    "NCT00840801",
    "NCT00847613",
    "NCT00853385",
    "NCT00856544",
    "NCT00863304",
    "NCT00863772",
    "NCT00864097",
    "NCT00868530",
    "NCT00883740",
    "NCT00887224",
    "NCT00904670",
    "NCT00932893",
    "NCT00960440",
    "NCT00974311",
    "NCT00985621",
    "NCT00991276",
    "NCT00996918",
    "NCT00998764",
    "NCT01026038",
    "NCT01035346",
    "NCT01039688",
    "NCT01049217",
    "NCT01057693",
    "NCT01073605",
    "NCT01077973",
    "NCT01098747",
    "NCT01100307",
    "NCT01103063",
    "NCT01112865",
    "NCT01154140",
    "NCT01186744",
    "NCT01212991",
    "NCT01216163",
    "NCT01232556",
    "NCT01237327",
    "NCT01258738",
    "NCT01262677",
    "NCT01266161",
    "NCT01270828",
    "NCT01270971",
    "NCT01271933",
    "NCT01276639",
    "NCT01302119",
    "NCT01309737",
    "NCT01332149",
    "NCT01335061",
    "NCT01360554",
    "NCT01362491",
    "NCT01371734",
    "NCT01372150",
    "NCT01387607",
    "NCT01389596",
    "NCT01432236",
    "NCT01438957",
    "NCT01441440",
    "NCT01455415",
    "NCT01458574",
    "NCT01458951",
    "NCT01465763",
    "NCT01473407",
    "NCT01473420",
    "NCT01474772",
    "NCT01557244",
    "NCT01564784",
    "NCT01571362",
    "NCT01595438",
    "NCT01599806",
    "NCT01639001",
    "NCT01654250",
    "NCT01701362",
    "NCT01720524",
    "NCT01726023",
    "NCT01740427",
    "NCT01747915",
    "NCT01763164",
    "NCT01774721",
    "NCT01794923",
    "NCT01808092",
    "NCT01815424",
    "NCT01877668",
    "NCT01882439",
    "NCT01888497",
    "NCT01942135",
    "NCT01945034",
    "NCT01945775",
    "NCT01968954",
    "NCT01968967",
    "NCT01968980",
    "NCT01975376",
    "NCT01975389",
    "NCT01989676",
    "NCT01994889",
    "NCT02003924",
    "NCT02072824",
    "NCT02075047",
    "NCT02100514",
    "NCT02118766",
    "NCT02118792",
    "NCT02130557",
    "NCT02135029",
    "NCT02213263",
    "NCT02297438",
    "NCT02364999",
    "NCT02458287",
    "NCT02504294",
    "NCT02528188",
    "NCT02528253",
    "NCT02580058",
    "NCT02592434",
    "NCT02603432",
    "NCT02609828",
    "NCT02697773",
    "NCT02709486",
    "NCT02718417",
    "NCT02761980",
    "NCT02837952",
    "NCT02863575",
    "NCT02912650",
    "NCT02928224",
    "NCT02952586",
    "NCT03052608",
    "NCT03090191",
    "NCT03235479",
    "NCT03237845",
    "NCT03349060",
    "NCT03395197",
    "NCT03416179",
    "NCT03439514",
    "NCT03461757",
    "NCT03486457",
    "NCT03502616",
    "NCT03575871",
    "NCT03627767",
    "NCT03720470",
    "NCT03796676",
    "NCT03831880",
    "NCT04040192",
    "NCT04345367",
    "NCT04360187",
    "NCT04571060",
    "NCT04574362",
]