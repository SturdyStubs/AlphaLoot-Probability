# AlphaLoot-Probability
Calculates the probability of your AlphaLoot tables

# How to Use
1. Drop your AlphaLoot table such as default_loottable.json into the project directory
2. Open the config and adjust the loot_files to include all loot tables you've inserted
3. Run by using `py main.py`

Default config:
```
{
    "loot_files": [
        "default_loottable.json",
        "default_heli_loottable.json",
        "default_bradley_loottable.json"
    ],
    "output_min_max_condition": true,
    "output_min_max_amount": true
}
```

output_min_max_condition - Outputs the min/max conditions of any items that have a condition applied
output_min_max_amount - Outputs the min/max amount of the item

Aggrevated Probability - The complete total probablity for an item without factoring in additional subdefinitions and multiple items
```
"rope": 22
```

Regular Probability - The probability of items with separation of subdefinitions
```
"rope,sewing kits": 11
"rope,metal pipes": 11
```