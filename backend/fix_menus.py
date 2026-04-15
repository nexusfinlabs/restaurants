import json

with open('agents/restaurants/data/menu.json', 'r') as f:
    data = json.load(f)

galleries = {
    "Raíces": [
        "https://images.pexels.com/photos/1092730/pexels-photo-1092730.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/7462417/pexels-photo-7462417.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/3331405/pexels-photo-3331405.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/4055246/pexels-photo-4055246.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1143754/pexels-photo-1143754.jpeg?auto=compress&cs=tinysrgb&w=800"
    ],
    "Marea": [
        "https://images.pexels.com/photos/560249/pexels-photo-560249.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1118146/pexels-photo-1118146.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/2034969/pexels-photo-2034969.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/11440056/pexels-photo-11440056.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/2813137/pexels-photo-2813137.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/6027402/pexels-photo-6027402.jpeg?auto=compress&cs=tinysrgb&w=800"
    ],
    "Brasa fina": [
        "https://images.pexels.com/photos/1639556/pexels-photo-1639556.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/3186831/pexels-photo-3186831.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1633524/pexels-photo-1633524.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/11055026/pexels-photo-11055026.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/6513725/pexels-photo-6513725.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/19623847/pexels-photo-19623847.jpeg?auto=compress&cs=tinysrgb&w=800"
    ],
    "Homenaje": [
        "https://images.pexels.com/photos/1126728/pexels-photo-1126728.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1614286/pexels-photo-1614286.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/6702206/pexels-photo-6702206.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1579739/pexels-photo-1579739.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/12392762/pexels-photo-12392762.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/5409020/pexels-photo-5409020.jpeg?auto=compress&cs=tinysrgb&w=800"
    ],
    "Verde absoluto": [
        "https://images.pexels.com/photos/1640775/pexels-photo-1640775.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/3850838/pexels-photo-3850838.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/403495/pexels-photo-403495.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1209025/pexels-photo-1209025.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/2446702/pexels-photo-2446702.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/327158/pexels-photo-327158.jpeg?auto=compress&cs=tinysrgb&w=800"
    ],
    "Chef's table": [
        "https://images.pexels.com/photos/1267320/pexels-photo-1267320.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/684964/pexels-photo-684964.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1013444/pexels-photo-1013444.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/254483/pexels-photo-254483.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1556066/pexels-photo-1556066.jpeg?auto=compress&cs=tinysrgb&w=800",
        "https://images.pexels.com/photos/1211887/pexels-photo-1211887.jpeg?auto=compress&cs=tinysrgb&w=800"
    ]
}

for item in data.get('menus_degustacion', []):
    item['gallery'] = galleries.get(item['nombre'], [])

with open('agents/restaurants/data/menu.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Menu fix done!")
