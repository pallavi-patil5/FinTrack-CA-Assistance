def calculate_roi(investment, net_profit):
    roi = (net_profit / investment) * 100 if investment else 0
    return {
        "investment": investment,
        "net_profit": net_profit,
        "roi_percent": round(roi, 2),
        "interpretation": "Good" if roi > 0 else "Loss"
    }

def calculate_profit_margin(revenue, cost):
    profit = revenue - cost
    margin = (profit / revenue) * 100 if revenue else 0
    return {
        "revenue": revenue,
        "cost": cost,
        "gross_profit": profit,
        "gross_margin_percent": round(margin, 2),
        "break_even": cost
    }

def calculate_cash_flow(inflows, outflows):
    total_in = sum(inflows)
    total_out = sum(outflows)
    net = total_in - total_out
    ratio = (total_out / total_in * 100) if total_in else 0

    return {
        "total_inflows": total_in,
        "total_outflows": total_out,
        "net_cash_flow": net,
        "operating_ratio": round(ratio, 2),
        "status": "Positive" if net >= 0 else "Negative"
    }

def calculate_emi(principal, annual_rate, tenure_months):
    r = annual_rate / (12 * 100)
    if r == 0:
        emi = principal / tenure_months if tenure_months else 0
    else:
        emi = principal * r * (1 + r)**tenure_months / ((1 + r)**tenure_months - 1)

    total_payment = emi * tenure_months
    total_interest = total_payment - principal

    return {
        "principal": principal,
        "annual_rate": annual_rate,
        "tenure_months": tenure_months,
        "emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2)
    }

def calculate_gst(base_amount, gst_rate, is_inclusive):
    if is_inclusive:
        gst_amount = base_amount - (base_amount / (1 + gst_rate/100))
        base = base_amount - gst_amount
    else:
        gst_amount = base_amount * gst_rate / 100
        base = base_amount

    return {
        "base_amount": round(base, 2),
        "gst_rate": gst_rate,
        "gst_amount": round(gst_amount, 2),
        "cgst": round(gst_amount / 2, 2),
        "sgst": round(gst_amount / 2, 2),
        "total_amount": round(base + gst_amount, 2),
        "type": "Inclusive" if is_inclusive else "Exclusive"
    }