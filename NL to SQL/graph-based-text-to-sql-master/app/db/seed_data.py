"""
Fixed seed data for the demo SQLite database — 5 tables, ~50 rows each.
All foreign keys are consistent. Data is realistic enough for demo queries:
  - top customers by order count
  - products with highest sales
  - monthly orders / revenue
  - employee performance
  - category-level aggregations
"""

# ------------------------------------------------------------------
# categories  (8 rows — referenced by products.category_id)
# ------------------------------------------------------------------
CATEGORIES = [
    (1, "Electronics",  "Computers, phones, audio, and smart devices"),
    (2, "Accessories",  "Cables, hubs, stands, and peripheral add-ons"),
    (3, "Furniture",    "Desks, chairs, shelves, and office furniture"),
    (4, "Mobile",       "Smartphones and tablets"),
    (5, "Networking",   "Routers, switches, and network hardware"),
    (6, "Storage",      "Hard drives, SSDs, and memory cards"),
    (7, "Audio",        "Speakers, headphones, and microphones"),
    (8, "Wearables",    "Smart watches and fitness trackers"),
]

# ------------------------------------------------------------------
# employees  (10 rows — referenced by orders.employee_id)
# ------------------------------------------------------------------
EMPLOYEES = [
    (1,  "Tom Bradley",    "Sales",     "2020-03-15"),
    (2,  "Sara Nguyen",    "Sales",     "2019-07-01"),
    (3,  "Mike Okafor",    "Sales",     "2021-01-10"),
    (4,  "Linda Park",     "Support",   "2018-11-20"),
    (5,  "James Ruiz",     "Sales",     "2022-05-05"),
    (6,  "Amy Chen",       "Logistics", "2020-08-14"),
    (7,  "David Patel",    "Sales",     "2021-09-30"),
    (8,  "Rachel Moore",   "Support",   "2019-04-22"),
    (9,  "Kevin Walsh",    "Sales",     "2023-02-01"),
    (10, "Nina Hoffman",   "Logistics", "2017-06-18"),
]

# ------------------------------------------------------------------
# customers  (50 rows)
# ------------------------------------------------------------------
CUSTOMERS = [
    (1,  "Alice Johnson",    "alice.johnson@example.com",    "USA"),
    (2,  "Bob Martinez",     "bob.martinez@example.com",     "Mexico"),
    (3,  "Carol White",      "carol.white@example.com",      "UK"),
    (4,  "David Kim",        "david.kim@example.com",        "South Korea"),
    (5,  "Emma Davis",       "emma.davis@example.com",       "Canada"),
    (6,  "Frank Chen",       "frank.chen@example.com",       "China"),
    (7,  "Grace Patel",      "grace.patel@example.com",      "India"),
    (8,  "Henry Brown",      "henry.brown@example.com",      "Australia"),
    (9,  "Isabella Lopez",   "isabella.lopez@example.com",   "Brazil"),
    (10, "James Wilson",     "james.wilson@example.com",     "USA"),
    (11, "Karen Taylor",     "karen.taylor@example.com",     "Germany"),
    (12, "Liam Anderson",    "liam.anderson@example.com",    "France"),
    (13, "Mia Thomas",       "mia.thomas@example.com",       "Japan"),
    (14, "Noah Jackson",     "noah.jackson@example.com",     "USA"),
    (15, "Olivia Harris",    "olivia.harris@example.com",    "UK"),
    (16, "Paul Martin",      "paul.martin@example.com",      "France"),
    (17, "Quinn Garcia",     "quinn.garcia@example.com",     "Spain"),
    (18, "Rachel Lee",       "rachel.lee@example.com",       "South Korea"),
    (19, "Samuel Walker",    "samuel.walker@example.com",    "USA"),
    (20, "Tina Hall",        "tina.hall@example.com",        "Canada"),
    (21, "Uma Allen",        "uma.allen@example.com",        "India"),
    (22, "Victor Young",     "victor.young@example.com",     "USA"),
    (23, "Wendy Hernandez",  "wendy.hernandez@example.com",  "Mexico"),
    (24, "Xander King",      "xander.king@example.com",      "UK"),
    (25, "Yara Wright",      "yara.wright@example.com",      "Australia"),
    (26, "Zoe Scott",        "zoe.scott@example.com",        "USA"),
    (27, "Aaron Torres",     "aaron.torres@example.com",     "Brazil"),
    (28, "Bella Nguyen",     "bella.nguyen@example.com",     "Vietnam"),
    (29, "Carlos Hill",      "carlos.hill@example.com",      "USA"),
    (30, "Diana Flores",     "diana.flores@example.com",     "Mexico"),
    (31, "Ethan Green",      "ethan.green@example.com",      "USA"),
    (32, "Fiona Adams",      "fiona.adams@example.com",      "Ireland"),
    (33, "George Nelson",    "george.nelson@example.com",    "UK"),
    (34, "Hannah Baker",     "hannah.baker@example.com",     "USA"),
    (35, "Ivan Carter",      "ivan.carter@example.com",      "Russia"),
    (36, "Julia Mitchell",   "julia.mitchell@example.com",   "USA"),
    (37, "Kevin Perez",      "kevin.perez@example.com",      "USA"),
    (38, "Laura Roberts",    "laura.roberts@example.com",    "Canada"),
    (39, "Mike Turner",      "mike.turner@example.com",      "USA"),
    (40, "Nancy Phillips",   "nancy.phillips@example.com",   "UK"),
    (41, "Oscar Campbell",   "oscar.campbell@example.com",   "USA"),
    (42, "Penny Parker",     "penny.parker@example.com",     "Australia"),
    (43, "Ray Evans",        "ray.evans@example.com",        "USA"),
    (44, "Sara Edwards",     "sara.edwards@example.com",     "Germany"),
    (45, "Tom Collins",      "tom.collins@example.com",      "USA"),
    (46, "Ursula Stewart",   "ursula.stewart@example.com",   "France"),
    (47, "Vincent Sanchez",  "vincent.sanchez@example.com",  "USA"),
    (48, "Wanda Morris",     "wanda.morris@example.com",     "Canada"),
    (49, "Xavier Rogers",    "xavier.rogers@example.com",    "USA"),
    (50, "Yvonne Reed",      "yvonne.reed@example.com",      "UK"),
]

# ------------------------------------------------------------------
# products  (50 rows — category_id references CATEGORIES)
# ------------------------------------------------------------------
PRODUCTS = [
    (1,  "MacBook Pro 14",        1,  1999.99),
    (2,  "Dell XPS 15",           1,  1749.99),
    (3,  "Logitech MX Master",    2,    99.99),
    (4,  "Mechanical Keyboard",   2,   149.99),
    (5,  "LG 27in 4K Monitor",    1,   599.99),
    (6,  "Sony WH-1000XM5",       7,   349.99),
    (7,  "Logitech C920 Webcam",  2,    79.99),
    (8,  "Standing Desk",         3,   499.99),
    (9,  "Ergonomic Chair",       3,   399.99),
    (10, "iPhone 15 Pro",         4,  1199.99),
    (11, "Samsung Galaxy S24",    4,   999.99),
    (12, "iPad Air",              4,   749.99),
    (13, "AirPods Pro",           7,   249.99),
    (14, "USB-C Hub 7-in-1",      2,    49.99),
    (15, "Portable SSD 1TB",      6,   109.99),
    (16, "Desk Lamp LED",         3,    39.99),
    (17, "Monitor Arm",           2,    59.99),
    (18, "Webcam Ring Light",     2,    29.99),
    (19, "Noise-Cancel Earbuds",  7,   179.99),
    (20, "Smart Watch Series 9",  8,   429.99),
    (21, "Wireless Charger Pad",  2,    35.99),
    (22, "Laptop Stand",          2,    45.99),
    (23, "Bookshelf 5-Tier",      3,   129.99),
    (24, "Filing Cabinet",        3,   189.99),
    (25, "Whiteboard 48x36",      3,    89.99),
    (26, "HDMI Cable 2m",         2,    14.99),
    (27, "Ethernet Cable 5m",     5,    12.99),
    (28, "Power Strip 6-Outlet",  2,    24.99),
    (29, "Desk Organizer",        3,    34.99),
    (30, "Cable Management Kit",  2,    19.99),
    (31, "Raspberry Pi 5",        1,    79.99),
    (32, "Arduino Mega",          1,    45.99),
    (33, "Portable Projector",    1,   449.99),
    (34, "Smart Speaker",         7,    99.99),
    (35, "Tablet Stand",          2,    27.99),
    (36, "Keyboard Wrist Rest",   2,    22.99),
    (37, "Mouse Pad XL",          2,    18.99),
    (38, "Laptop Backpack",       2,    79.99),
    (39, "Screen Cleaner Kit",    2,     9.99),
    (40, "Thermal Paste",         2,     8.99),
    (41, "Mini PC Intel N100",    1,   299.99),
    (42, "NAS Drive 4TB",         6,   349.99),
    (43, "Gaming Headset",        7,   129.99),
    (44, "Stream Deck Mini",      1,    99.99),
    (45, "Drawing Tablet",        1,   249.99),
    (46, "Conference Speakerphone",7,  199.99),
    (47, "Desk Mat Leather",      3,    54.99),
    (48, "Monitor Light Bar",     2,    49.99),
    (49, "Fingerprint USB Key",   2,    39.99),
    (50, "Portable Power Bank",   4,    59.99),
]

# ------------------------------------------------------------------
# orders  (50 rows)
# Columns: order_id, customer_id, product_id, employee_id, quantity, order_date
# Weighted so top customers / products / employees are clear for demo queries
# ------------------------------------------------------------------
ORDERS = [
    (1,  1,  10, 1, 3, "2024-01-05"),
    (2,  1,   5, 2, 1, "2024-01-12"),
    (3,  1,  13, 1, 2, "2024-02-03"),
    (4,  2,   1, 3, 1, "2024-01-08"),
    (5,  2,   6, 2, 1, "2024-02-14"),
    (6,  3,   4, 1, 2, "2024-01-20"),
    (7,  3,   9, 4, 1, "2024-03-01"),
    (8,  3,  20, 2, 1, "2024-03-15"),
    (9,  4,   2, 3, 1, "2024-02-07"),
    (10, 4,  12, 5, 2, "2024-04-10"),
    (11, 5,   3, 1, 3, "2024-01-25"),
    (12, 5,   7, 2, 1, "2024-02-28"),
    (13, 5,  14, 1, 4, "2024-03-20"),
    (14, 5,  22, 3, 1, "2024-04-05"),
    (15, 6,   8, 6, 1, "2024-02-10"),
    (16, 6,  11, 2, 1, "2024-03-08"),
    (17, 7,   5, 7, 2, "2024-01-30"),
    (18, 7,  19, 1, 1, "2024-04-18"),
    (19, 8,   6, 2, 1, "2024-02-22"),
    (20, 8,  33, 3, 1, "2024-05-01"),
    (21, 9,  10, 1, 1, "2024-03-12"),
    (22, 9,  45, 5, 1, "2024-05-10"),
    (23, 10,  1, 2, 1, "2024-01-15"),
    (24, 10,  4, 7, 1, "2024-02-19"),
    (25, 10, 13, 1, 1, "2024-03-25"),
    (26, 11,  2, 3, 1, "2024-04-02"),
    (27, 11, 42, 9, 1, "2024-05-15"),
    (28, 12,  5, 2, 1, "2024-02-05"),
    (29, 12, 20, 1, 2, "2024-04-22"),
    (30, 13,  9, 4, 1, "2024-03-03"),
    (31, 14,  3, 1, 2, "2024-01-18"),
    (32, 14, 17, 7, 1, "2024-04-30"),
    (33, 15,  6, 2, 1, "2024-02-25"),
    (34, 16, 11, 3, 1, "2024-03-18"),
    (35, 17,  1, 9, 1, "2024-05-05"),
    (36, 18,  8, 6, 1, "2024-04-14"),
    (37, 19, 50, 1, 2, "2024-05-20"),
    (38, 20,  4, 2, 1, "2024-03-28"),
    (39, 21, 13, 5, 1, "2024-04-08"),
    (40, 22,  5, 7, 3, "2024-05-12"),
    (41, 23,  2, 3, 1, "2024-02-16"),
    (42, 24, 10, 1, 1, "2024-03-22"),
    (43, 25,  6, 2, 1, "2024-04-25"),
    (44, 26,  1, 9, 2, "2024-05-08"),
    (45, 27, 20, 1, 1, "2024-03-10"),
    (46, 28,  9, 4, 1, "2024-04-16"),
    (47, 29,  3, 1, 1, "2024-05-22"),
    (48, 30,  5, 2, 2, "2024-02-20"),
    (49, 31, 13, 5, 1, "2024-04-28"),
    (50, 32,  6, 7, 1, "2024-05-18"),
]
