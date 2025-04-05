import requests

API_URL = "https://api.platform.opentargets.org/api/v4/graphql"
TARGET_GENE = "ENSG00000141510"  # TP53

def build_query():
    query = f"""
    {{
      target(ensemblId: "{TARGET_GENE}") {{
        knownDrugs {{
          count
          rows {{
            drug {{
              id
              name
            }}
            disease {{
              id
              name
            }}
          }}
        }}
      }}
    }}
    """
    return query


def query_open_targets_api():
    graphql_query = build_query()
    payload = {"query": graphql_query}
    headers = {"Content-Type": "application/json"}

    response = requests.post(API_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.reason}")
    return response.json()


def parse_drug_evidence(response_json):
    try:
        known_drugs = response_json["data"]["target"]["knownDrugs"]
        count = known_drugs["count"]
        rows = known_drugs["rows"]

        results = {
            "target_gene": TARGET_GENE,
            "count": count,
            "rows": []
        }
        for row in rows:
            drug = row["drug"]
            disease = row["disease"]
            results["rows"].append({
                "drug_name": drug["name"],
                "drug_id": drug["id"],
                "disease_name": disease["name"],
                "disease_id": disease["id"]
            })
        return results
    except (KeyError, TypeError) as e:
        raise Exception("Failed to parse API response: " + str(e))


def display_drug_evidence(data):
    print("\n=== OpenTargets Drug Evidence ===")
    print("Target Gene: TP53 (" + TARGET_GENE + ")")
    print("Total Associations Found: " + str(data["count"]))
    print("================================\n")

    for item in data["rows"]:
        print("Drug:    " + item["drug_name"])
        print("ID:      " + item["drug_id"])
        print("Disease: " + item["disease_name"])
        print("ID:      " + item["disease_id"])
        print("--------------------------------")