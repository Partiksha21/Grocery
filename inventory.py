from flask import Flask, render_template, request, redirect, session, url_for, flash
import json, time

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session handling

@app.route('/')
def home():
    with open('records.json', 'r') as f:
        record = json.load(f)
    return render_template("index.html", record=record)

@app.route('/buy', methods=['POST'])
def buy():
    ui_pr = request.form["product_id"]
    ui_qn = int(request.form["quantity"])

    with open('records.json', 'r') as f:
        record = json.load(f)

    if ui_pr not in record or record[ui_pr]["Qn"] == 0:
        return render_template("result.html", result={"status": "fail", "message": "Product not available."})

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    if ui_pr in cart:
        cart[ui_pr] += ui_qn
    else:
        cart[ui_pr] = ui_qn

    session["cart"] = cart
    flash("Item added to cart successfully!")
    return redirect(url_for("cart"))

@app.route('/remove/<product_id>')
def remove_item(product_id):
    cart = session.get("cart", {})
    if product_id in cart:
        cart.pop(product_id)
        session["cart"] = cart
        flash("Item removed from cart.")
    return redirect(url_for("cart"))

@app.route('/cart')
def cart():
    with open('records.json', 'r') as f:
        record = json.load(f)

    cart = session.get("cart", {})
    cart_items = []
    total = 0
    gst_total = 0

    for pid, qty in cart.items():
        product = record[pid]
        price = product["Price"]
        gst = price * 0.05
        total_amount= (price ) * qty
        total_price = total_amount + gst
        total += total_price
        cart_items.append({
            "id": pid,
            "name": product["Name"],
            "price": price,
            "gst": gst,
            "quantity": qty,
            "total_price": total_price
        })

    return render_template("cart.html", cart_items=cart_items, total=total, gst_total=gst_total)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'GET':
        return render_template("checkout.html")

    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]

    with open('records.json', 'r') as f:
        record = json.load(f)

    cart = session.get("cart", {})
    if not cart:
        return render_template("result.html", result={"status": "fail", "message": "Cart is empty."})

    total = 0
    sale_entries = []

    for pid, qty in cart.items():
        if pid in record and record[pid]["Qn"] >= qty:
            price = record[pid]["Price"]
            billing = price * qty
            record[pid]["Qn"] -= qty
            total += billing
            sale_line = f"1,{name},{email},{phone},{pid},{record[pid]['Name']},{qty},{price},{price*qty},{time.ctime()}\n"
            sale_entries.append(sale_line)
        else:
            return render_template("result.html", result={"status": "fail", "message": f"Insufficient stock for {record[pid]['Name']}"})

    # Apply discounts
    msg = ""
    total_after_discount=0
    gst = total * 0.05
    total += gst
    if total >= 7000:
        discount = total * 0.10
        total_after_discount= total-discount
        msg = "You got a 10% discount"
    elif total >= 5000:
        total_after_discount = total-500
        msg = "You got a flat ₹500 discount"

    with open("records.json", "w") as f:
        json.dump(record, f)

    with open("Sales.txt", "a") as f:
        f.writelines(sale_entries)

    session.pop("cart", None)

    result = {
    "status": "success",
    "name": name,
    "email": email,
    "phone": phone,
    "items": len(cart),
    "gst": gst,
    "total_after_discount": total_after_discount,
    "billing": total,
    "discount_note": msg,
    "products": [{
        "name": record[pid]['Name'],
        "price": record[pid]['Price'],
        "quantity": qty
    } for pid, qty in cart.items()]
}



    return render_template("result.html", result=result)

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
