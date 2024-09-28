import json
import os
from collections import defaultdict

# Create config file if non-existent
def check_or_create_config(config_file):
    if not os.path.exists(config_file):
        print(f"Config file '{config_file}' not found. Generating a default config...")

        default_config = {
            "loot_files": [
                "default_loottable.json",
                "default_heli_loottable.json",
                "default_bradley_loottable.json"
            ],
            "output_min_max_condition": True,
            "output_min_max_amount": True
        }

        with open(config_file, 'w') as file:
            json.dump(default_config, file, indent=4)

        print(f"Default config created. Please update '{config_file}' if necessary.")
        return False
    return True

def load_loot_table(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def calculate_subspawn_percentage(subspawn_list, parent_probability=1.0, output_min_max_condition=True, output_min_max_amount=True):
    total_weight = sum(subspawn.get("Weight", 0) for subspawn in subspawn_list)
    if total_weight == 0:
        total_weight = 1  # Prevent division by zero

    percentages = {}
    amounts = {}

    for subspawn in subspawn_list:
        if "Probability" in subspawn:
            subspawn_probability = subspawn["Probability"] * parent_probability
        else:
            subspawn_probability = (subspawn.get("Weight", 1) / total_weight) * parent_probability

        if "Category" in subspawn and subspawn["Category"].get("Items"):
            item_combination = []
            min_combination_amounts = {}
            max_combination_amounts = {}
            conditions = {}

            for item in subspawn["Category"]["Items"]:
                shortname = item.get("Shortname", "Unknown")
                max_amount = item.get("MaxAmount", 1)
                min_amount = item.get("MinAmount", 1)
                condition = item.get("Condition", {})

                item_combination.append(shortname)
                if output_min_max_amount:
                    min_combination_amounts[shortname] = min_amount
                    max_combination_amounts[shortname] = max_amount
                if output_min_max_condition:
                    conditions[shortname] = {
                        "MinCondition": condition.get("MinCondition", None),
                        "MaxCondition": condition.get("MaxCondition", None)
                    }

            combination_key = ",".join(item_combination)
            rounded_probability = round(subspawn_probability * 100, 2)

            if combination_key in percentages:
                percentages[combination_key] += rounded_probability
            else:
                percentages[combination_key] = rounded_probability

            if combination_key in amounts:
                for shortname in item_combination:
                    if output_min_max_amount:
                        amounts[combination_key]["Max"][shortname] = max(amounts[combination_key]["Max"].get(shortname, 0), max_combination_amounts[shortname])
                        amounts[combination_key]["Min"][shortname] = min(amounts[combination_key]["Min"].get(shortname, float('inf')), min_combination_amounts[shortname])
                    if output_min_max_condition:
                        amounts[combination_key]["Condition"][shortname] = conditions[shortname]
            else:
                amounts[combination_key] = {
                    "Min": min_combination_amounts if output_min_max_amount else {},
                    "Max": max_combination_amounts if output_min_max_amount else {},
                    "Condition": conditions if output_min_max_condition else {}
                }

        if "SubSpawn" in subspawn["Category"] and subspawn["Category"]["SubSpawn"]:
            nested_percentages, nested_amounts = calculate_subspawn_percentage(subspawn["Category"]["SubSpawn"], subspawn_probability, output_min_max_condition, output_min_max_amount)
            for combination, nested_percentage in nested_percentages.items():
                rounded_nested_percentage = round(nested_percentage, 2)
                if combination in percentages:
                    percentages[combination] += rounded_nested_percentage
                else:
                    percentages[combination] = rounded_nested_percentage

            for combination, nested_amount in nested_amounts.items():
                if combination in amounts:
                    for shortname in nested_amount["Min"]:
                        if output_min_max_amount:
                            amounts[combination]["Max"][shortname] = max(amounts[combination]["Max"].get(shortname, 0), nested_amount["Max"][shortname])
                            amounts[combination]["Min"][shortname] = min(amounts[combination]["Min"].get(shortname, float('inf')), nested_amount["Min"][shortname])
                        if output_min_max_condition:
                            amounts[combination]["Condition"][shortname] = nested_amount["Condition"][shortname]
                else:
                    amounts[combination] = nested_amount

    return percentages, amounts

def calculate_loot_probabilities(loot_table, output_min_max_condition=True, output_min_max_amount=True):
    loot_probabilities = {}

    for container, details in loot_table.get("loot_advanced", {}).items():
        container_probabilities = {}
        container_amounts = {}
        loops = details.get("Loops", 1)

        for slot in details.get("LootSpawnSlots", []):
            subspawns = slot["LootDefinition"].get("SubSpawn", [])

            parent_probability = slot.get("Probability", 1)

            if not subspawns and slot["LootDefinition"].get("Items"):
                percentages = {}
                amounts = {}

                item_combination = []
                min_combination_amounts = {}
                max_combination_amounts = {}
                conditions = {}

                for item in slot["LootDefinition"]["Items"]:
                    shortname = item.get("Shortname", "Unknown")
                    max_amount = item.get("MaxAmount", 1)
                    min_amount = item.get("MinAmount", 1)
                    condition = item.get("Condition", {})

                    item_combination.append(shortname)
                    if output_min_max_amount:
                        min_combination_amounts[shortname] = min_amount
                        max_combination_amounts[shortname] = max_amount
                    if output_min_max_condition:
                        conditions[shortname] = {
                            "MinCondition": condition.get("MinCondition", None),
                            "MaxCondition": condition.get("MaxCondition", None)
                        }

                combination_key = ",".join(item_combination)
                rounded_probability = round(parent_probability * 100, 2)

                percentages[combination_key] = rounded_probability
                amounts[combination_key] = {
                    "Min": min_combination_amounts if output_min_max_amount else {},
                    "Max": max_combination_amounts if output_min_max_amount else {},
                    "Condition": conditions if output_min_max_condition else {}
                }
            else:
                percentages, amounts = calculate_subspawn_percentage(subspawns, parent_probability, output_min_max_condition, output_min_max_amount)

            for combination, percentage in percentages.items():
                final_percentage = round(percentage * loops, 2)
                if combination in container_probabilities:
                    container_probabilities[combination] += final_percentage
                else:
                    container_probabilities[combination] = final_percentage

            for combination, amount in amounts.items():
                if combination in container_amounts:
                    for shortname in amount["Min"]:
                        if output_min_max_amount:
                            container_amounts[combination]["Max"][shortname] = max(container_amounts[combination]["Max"].get(shortname, 0), amount["Max"][shortname])
                            container_amounts[combination]["Min"][shortname] = min(container_amounts[combination]["Min"].get(shortname, float('inf')), amount["Min"][shortname])
                        if output_min_max_condition:
                            container_amounts[combination]["Condition"][shortname] = amount["Condition"][shortname]
                else:
                    container_amounts[combination] = amount

        scrap_info = {
            "MinScrap": details.get("MinScrapAmount", 0),
            "MaxScrap": details.get("MaxScrapAmount", 0)
        }

        for combination, percentage in container_probabilities.items():
            container_probabilities[combination] = round(percentage, 2)

        loot_probabilities[container] = {
            "Probabilities": container_probabilities,
            "Amounts": container_amounts,
            "ScrapInfo": scrap_info
        }

    return loot_probabilities

def aggregate_item_probabilities(loot_probabilities, output_min_max_condition=True, output_min_max_amount=True):
    aggregated_probabilities = {}

    for container, details in loot_probabilities.items():
        item_probabilities = defaultdict(float)
        item_amounts = defaultdict(lambda: {"Min": float('inf'), "Max": 0, "MinCondition": None, "MaxCondition": None})

        for combination, probability in details["Probabilities"].items():
            items = combination.split(",")  # Split multi-item combinations
            for item in items:
                item_probabilities[item] += probability
                if output_min_max_amount:
                    item_amounts[item]["Min"] = min(item_amounts[item]["Min"], details["Amounts"][combination]["Min"][item])
                    item_amounts[item]["Max"] = max(item_amounts[item]["Max"], details["Amounts"][combination]["Max"][item])
                if output_min_max_condition and "Condition" in details["Amounts"][combination]:
                    condition = details["Amounts"][combination]["Condition"].get(item, {})
                    if condition.get("MinCondition") is not None:
                        item_amounts[item]["MinCondition"] = condition["MinCondition"]
                    if condition.get("MaxCondition") is not None:
                        item_amounts[item]["MaxCondition"] = condition["MaxCondition"]

        aggregated_probabilities[container] = {
            "Probabilities": {item: round(prob, 2) for item, prob in item_probabilities.items()},
            "Amounts": item_amounts
        }

    return aggregated_probabilities

def save_loot_probabilities_as_json(loot_probabilities, output_file, round_percentages=False):
    os.makedirs("Output", exist_ok=True)
    output_path = os.path.join("Output", output_file)

    if round_percentages:
        for container, details in loot_probabilities.items():
            if "Probabilities" in details:
                for item, prob in details["Probabilities"].items():
                    rounded_prob = round(prob * 2) / 2
                    print(f"Rounding {item}: {prob} -> {rounded_prob}") # debug
                    details["Probabilities"][item] = rounded_prob

    with open(output_path, 'w') as file:
        json.dump(loot_probabilities, file, indent=4)

def process_loot_files(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)

    output_min_max_condition = config.get("output_min_max_condition", True)
    output_min_max_amount = config.get("output_min_max_amount", True)
    round_percentages = config.get("round_percentages", False)

    for loot_file in config["loot_files"]:
        input_file = loot_file
        
        if not os.path.exists(input_file):
            print(f"File '{input_file}' not found. Skipping.")
            continue

        output_file = f"{os.path.splitext(os.path.basename(input_file))[0]}_probability.json"
        aggregated_output_file = f"{os.path.splitext(os.path.basename(input_file))[0]}_aggregated_probability.json"

        print(f"Processing {input_file}...")
        loot_table = load_loot_table(input_file)
        loot_probabilities = calculate_loot_probabilities(loot_table, output_min_max_condition, output_min_max_amount)
        aggregated_probabilities = aggregate_item_probabilities(loot_probabilities, output_min_max_condition, output_min_max_amount)

        save_loot_probabilities_as_json(loot_probabilities, output_file, round_percentages)
        save_loot_probabilities_as_json(aggregated_probabilities, aggregated_output_file, round_percentages)

        print(f"Saved loot probabilities to 'Output/{output_file}'")
        print(f"Saved aggregated loot probabilities to 'Output/{aggregated_output_file}'")

if __name__ == "__main__":
    config_file = 'config.json'
    
    if check_or_create_config(config_file):
        process_loot_files(config_file)
    else:
        print(f"File error for '{config_file}'. This may not be an AlphaLoot data file.")