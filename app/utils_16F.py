import re


def safe_get(d, keys, default=""):
    """
    Attempt to get a value from a nested dictionary(d) using a list of keys.
    Returns the value if found, else returns default (an empty string).
    """
    for key in keys:
        try:
            d = d.get(key, default)
        except AttributeError:
            return default
    return d


def extract_from_json(clinical_study):
    # 0. Subset JSON
    extracted_json = {}

    # 1. PROTOCOL SECTION
    protocol_section = clinical_study.get("protocolSection", {})

    # 1.1. IDENTIFICATION MODULE
    identification_module = protocol_section.get("identificationModule", {})
    extracted_json = {
        "National Clinical Identification NCT ID": safe_get(identification_module, ["nctId"]),
        "Organization study identification": safe_get(identification_module, ["orgStudyIdInfo", "id"]),
        "EudraCT number": f"""{safe_get(identification_module, ["secondaryIdInfos"])[0]["id"]}""",
        "Organization": safe_get(identification_module, ["organization", "fullName"]),
        "Organization class": safe_get(identification_module, ["organization", "class"]),
        "Brief title": safe_get(identification_module, ["briefTitle"]),
        "Official title": safe_get(identification_module, ["officialTitle"]),
    }

    # 1.2. STATUS MODULE
    status_module = protocol_section.get("statusModule",
                                         {})  # Make sure this is correctly pointing to your data structure
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
        "Condition": f"""{safe_get(conditions_module, ["conditions"])}""",
        "Conditions keywords": f"""{safe_get(conditions_module, ["keywords"])}""",
    })

    # 1.6. DESIGN MODULE
    design_module = protocol_section.get("designModule", {})
    extracted_json.update({
        "Study type": safe_get(design_module, ["studyType"]),
        "Phases": f"""{safe_get(design_module, ["phases"])}""",
        "Allocation": safe_get(design_module, ["designInfo", "allocation"]),
        "Intervention model": safe_get(design_module, ["designInfo", "interventionModel"]),
        "Primary purpose": safe_get(design_module, ["designInfo", "primaryPurpose"]),
        "Masking": safe_get(design_module, ["designInfo", "maskingInfo", "masking"]),
        "Who is masked": f"""{safe_get(design_module, ["designInfo", "maskingInfo", "whoMasked"])}""",
        "Enrollment count": f"""Enrollment count is {safe_get(design_module, ["enrollmentInfo", "count"])}""",
        "Enrollment type": safe_get(design_module, ["enrollmentInfo", "type"]),
    })

    # 1.7. ARMS INTERVENTIONS MODULE
    arms_interventions_module = protocol_section.get("armsInterventionsModule", {})
    arms_groups = safe_get(arms_interventions_module, ["armGroups"])
    interventions = safe_get(arms_interventions_module, ["interventions"])
    extracted_json.update({
        "Arms group 0 label": f"""{arms_groups[0]["label"]}""",
        "Arms group 0 type": f"""{arms_groups[0]["type"]}""",
        # "Arms group 0 description": f"""{safe_get(arms_interventions_module, ["armGroups"])[0]["description"]}"""
        "Arms group 0 intervention names": f"""{arms_groups[0]["interventionNames"]}""",
        "Arms group 1 label": f"""{arms_groups[1]["label"]}""",
        "Arms group 1 type": f"""{arms_groups[1]["type"]}""",
        #     "Arms group 1 description": f"""{safe_get(arms_interventions_module, ["armGroups"])[1]["description"]}"""
        "Arms group 1 intervention names": f"""{arms_groups[1]["interventionNames"]}""",

        "Arms group 0 intervention type": f"""{interventions[0]["type"]}""",
        "Arms group 0 intervention name": f"""{interventions[0]["name"]}""",
        # "Arms group 0 intervention description": f"""{safe_get(arms_interventions_module, ["interventions"])[0]["description"]}"""
        "Arms group 0 intervention labels": f"""{interventions[0]["armGroupLabels"]}""",
        "Arms group 1 intervention type": f"""{interventions[1]["type"]}""",
        "Arms group 1 intervention name": f"""{interventions[1]["name"]}""",
        # "Arms group 1 intervention description": f"""{safe_get(arms_interventions_module, ["interventions"])[1]["description"]}"""
        "Arms group 1 intervention labels": f"""{interventions[1]["armGroupLabels"]}""",
    })

    # 1.8. OUTCOMES MODULE
    outcomes_module = protocol_section.get("outcomesModule", {})
    primary_outcomes = safe_get(outcomes_module, ["primaryOutcomes"])
    extracted_json.update({
        "Primary outcome": primary_outcomes[0]["measure"],
        "Primary outcome description": primary_outcomes[0]["description"]
        if "description" in primary_outcomes[0] else "",
        "Primary outcome time frame": primary_outcomes[0]["timeFrame"],
    })
    secondary_outcomes = safe_get(outcomes_module, ["secondaryOutcomes"])
    for i in range(len(secondary_outcomes)):
        sec_outcome_dict = {
            f"Secondary outcome {i} measure": secondary_outcomes[i]["measure"],
            f"Secondary outcome {i} description": secondary_outcomes[i]["description"]
            if "description" in secondary_outcomes[i] else "",
            f"Secondary outcome {i} time frame": secondary_outcomes[i]["timeFrame"],
        }
        extracted_json.update(sec_outcome_dict)

    # 1.9. ELIGIBILITY MODULE
    eligibility_module = protocol_section.get("eligibilityModule", {})
    extracted_json.update({
        # "Eligibility criteria": f"""{safe_get(eligibility_module, ["eligibilityCriteria"])}""",
        "Eligibility of healthy volunteer": f"""{safe_get(eligibility_module, ["healthyVolunteers"])}""",
        "Eligibility sex": f"""{safe_get(eligibility_module, ["sex"])}""",
        "Eligibility minimum age": f"""{safe_get(eligibility_module, ["minimumAge"])}""",
        "Eligibility standard age": f"""{safe_get(eligibility_module, ["stdAges"])}""",
    })

    # 2. RESULTS SECTION
    results_section = clinical_study.get("resultsSection", {})
    extracted_json.update({
        "Pre-assignment details": safe_get(results_section, ["participantFlowModule", "preAssignmentDetails"]),
        "Recruitment details": safe_get(results_section, ["participantFlowModule", "recruitmentDetails"]),
        "Recruitment group 0 id": safe_get(results_section, ["participantFlowModule", "groups"])[0]["id"],
        "Recruitment group 0 title": safe_get(results_section, ["participantFlowModule", "groups"])[0]["title"],
        "Recruitment group 0 description": safe_get(results_section, ["participantFlowModule", "groups"])[0][
            "description"],
        "Recruitment group 1 id": safe_get(results_section, ["participantFlowModule", "groups"])[1]["id"],
        "Recruitment group 1 title": safe_get(results_section, ["participantFlowModule", "groups"])[1]["title"],
        "Recruitment group 1 description": safe_get(results_section, ["participantFlowModule", "groups"])[1][
            "description"],

    })

    # 2.1. OUTCOMES MEASURES MODULE
    outcome_measures_module = results_section.get("outcomeMeasuresModule", {})
    outcome_measures = safe_get(outcome_measures_module, ["outcomeMeasures"])
    try:
        extracted_json.update({
            "Primary outcome group identifications": f"""{outcome_measures[0]["analyses"][0]["groupIds"]}""",
            "Primary outcome group description": f"""{outcome_measures[0]["analyses"][0]["groupDescription"]}""",
        })
    except:
        pass

    try:
        extracted_json.update({
            "Primary outcome group p-value": f"""{outcome_measures[0]["analyses"][0]["pValue"]}""",
            "Primary outcome group statistical method": f"""{outcome_measures[0]["analyses"][0]["statisticalMethod"]}""",
            "Primary outcome group statistical method parameter type": f"""{outcome_measures[0]["analyses"][0]["paramType"]}""",
            "Primary outcome group statistical method parameter value": f"""{outcome_measures[0]["analyses"][0]["paramValue"]}""",
        })
    except:
        pass

    try:
        extracted_json.update({
            "Primary outcome group confidence interval percentage value": f"""{outcome_measures[0]["analyses"][0]["ciPctValue"]}""",
            "Primary outcome group confidence interval lower limit": f"""{outcome_measures[0]["analyses"][0]["ciLowerLimit"]}""",
            "Primary outcome group confidence interval upper limit": f"""{outcome_measures[0]["analyses"][0]["ciUpperLimit"]}""",
            "Primary outcome group estimate comment": f"""{outcome_measures[0]["analyses"][0]["estimateComment"]}""",
        })
    except:
        pass

    # 2.2. MORE INFO MODULE
    more_info_module = results_section.get("moreInfoModule", {})
    extracted_json.update({
        "Limitations and caveats": f"""{safe_get(more_info_module, ["limitationsAndCaveats", "description"])}""",
    })

    # 3 HAS RESULTS SECTION
    has_results_section = clinical_study.get("hasResults", {})
    extracted_json.update({
        "Has results": f""" Does have results, {has_results_section}"""

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
