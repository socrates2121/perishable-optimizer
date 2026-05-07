# ============================================================
# Perishable Inventory Optimizer
# ============================================================

from fastapi import FastAPI
from scipy.stats import poisson

app = FastAPI()

# ============================================================
# ΔΕΔΟΜΕΝΑ ΠΡΟΪΟΝΤΩΝ
# ============================================================

products = [
    {
        "title":        "Γάλα",
        "stock":        15,
        "daily_demand": 5,
        "expiry_days":  3,
        "h_base":       0.02,
        "stockout":     0.80,
        "spoilage":     1.00
    },
    {
        "title":        "Κοτόπουλο",
        "stock":        8,
        "daily_demand": 4,
        "expiry_days":  2,
        "h_base":       0.10,
        "stockout":     3.50,
        "spoilage":     5.00
    },
    {
        "title":        "Σολομός",
        "stock":        5,
        "daily_demand": 3,
        "expiry_days":  1,
        "h_base":       0.25,
        "stockout":     8.00,
        "spoilage":     11.00
    },
    {
        "title":        "Φέτα",
        "stock":        20,
        "daily_demand": 2,
        "expiry_days":  7,
        "h_base":       0.05,
        "stockout":     2.50,
        "spoilage":     3.50
    },
    {
        "title":        "Σπανάκι",
        "stock":        10,
        "daily_demand": 6,
        "expiry_days":  2,
        "h_base":       0.03,
        "stockout":     0.60,
        "spoilage":     0.80
    }
]

# ============================================================
# ΣΥΝΑΡΤΗΣΕΙΣ ΒΕΛΤΙΣΤΟΠΟΙΗΣΗΣ
# ============================================================

def expected_cost(q, lam, r, h_base, stockout, spoilage):
    """Υπολογισμός αναμενόμενου κόστους για δεδομένο q."""
    
    h     = h_base * (1 / r)   # holding cost αυξάνεται όσο πλησιάζει λήξη
    p     = spoilage * (1 / r) # spoilage cost ίδια λογική
    max_d = int(lam * 4)       # ρεαλιστικό όριο ζήτησης
    
    exp_stockout = sum((d - q) * poisson.pmf(d, lam) 
                       for d in range(q + 1, max_d))
    
    exp_spoilage = sum((q - d) * poisson.pmf(d, lam) 
                       for d in range(0, q + 1))
    
    return round(h * q + stockout * exp_stockout + p * exp_spoilage, 4)


def find_optimal_q(lam, r, h_base, stockout, spoilage):
    """Grid search — δοκιμάζει όλα τα q και επιλέγει το καλύτερο."""
    
    best_q, best_cost = 0, float('inf')
    
    for q in range(0, int(lam * 3)):
        cost = expected_cost(q, lam, r, h_base, stockout, spoilage)
        if cost < best_cost:
            best_cost = cost
            best_q    = q
    
    return best_q, best_cost

#for product in products:
    q_star, min_cost = find_optimal_q(
        lam      = product['daily_demand'],
        r        = product['expiry_days'],
        h_base   = product['h_base'],
        stockout = product['stockout'],
        spoilage = product['spoilage']
    )
    print(f"{product['title']:15} → q* = {q_star} μονάδες | E[cost] = €{min_cost}")

# ============================================================
# FASTAPI — ENDPOINT
# ============================================================

@app.get("/optimize_all")
def optimize_all():
    """Επιστρέφει βέλτιστο q* για όλα τα προϊόντα μαζί."""
    
    results = []
    
    for product in products:
        q_star, min_cost = find_optimal_q(
            lam      = product['daily_demand'],
            r        = product['expiry_days'],
            h_base   = product['h_base'],
            stockout = product['stockout'],
            spoilage = product['spoilage']
        )
        results.append({
            "title":    product['title'],
            "q_star":   q_star,
            "min_cost": min_cost,
            "message":  f"Παράγγειλε {q_star} μονάδες {product['title']}"
        })
    
    return results