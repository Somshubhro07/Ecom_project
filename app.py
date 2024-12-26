from flask import Flask, render_template, request, redirect, session
import sqlite3
import flask
from flask import *
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database connection
def get_db_connection():
    conn = sqlite3.connect("user.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def main_page():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Retrieve search term and category filter from request arguments
    search_term = request.args.get("query", "").strip()
    category_id = request.args.get("category_id")

    # Base query to fetch approved products
    query = "SELECT * FROM product WHERE approve = 1"
    params = []

    # Add search term condition if provided
    if search_term:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])

    # Add category filter if provided
    if category_id:
        query += " AND category_id = ?"
        params.append(category_id)

    # Execute the query with any provided parameters
    products = cursor.execute(query, tuple(params)).fetchall()

    # Get delivery city for logged-in users
    delivery_city = None
    if 'user_id' in session:
        address = cursor.execute("""
            SELECT city FROM address 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (session['user_id'],)).fetchone()
        if address:
            delivery_city = address['city']

    # Get all categories for filtering
    categories = cursor.execute("SELECT * FROM categories").fetchall()

    conn.close()

    # Render the main page with products and filters
    return render_template(
        'main-page.html', 
        products=products, 
        delivery_city=delivery_city, 
        categories=categories, 
        search_term=search_term, 
        selected_category=category_id
    )



@app.route('/search_suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify([])  # Return an empty list for empty input

    conn = get_db_connection()
    cursor = conn.cursor()

    # Search for products and include category context
    suggestions = cursor.execute(
        """
        SELECT p.name AS product_name, c.name AS category_name
        FROM product p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.approve = 1 AND (p.name LIKE ? OR p.description LIKE ?)
        LIMIT 10
        """,
        (f"%{query}%", f"%{query}%")
    ).fetchall()

    conn.close()

    # Format suggestions
    suggestion_list = [
        {"product_name": suggestion["product_name"], "category_name": suggestion["category_name"] or "N/A"}
        for suggestion in suggestions
    ]

    return jsonify(suggestion_list)




@app.route("/product<int:product_id>")
def product_details(product_id):
    conn = get_db_connection()

    # Fetch product details
    product = conn.execute(
        "SELECT * FROM product WHERE id = ?", (product_id,)
    ).fetchone()

    # Check if product exists
    if not product:
        conn.close()
        return "Product not found", 404

    # Fetch delivery city for logged-in users
    delivery_city = None
    if "user_id" in session:
        address = conn.execute(
            """
            SELECT city FROM address 
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (session["user_id"],),
        ).fetchone()
        if address:
            delivery_city = address["city"]

    # Fetch categories for the navigation or display
    categories = conn.execute("SELECT * FROM categories").fetchall()

    # Calculate the discounted price
    discounted_price = (
        product["price"] - (product["price"] * product["discount"] / 100)
        if product["discount"]
        else product["price"]
    )

    # Parse image paths (comma-separated) into a list
    image_paths = product["image"].split(",") if product["image"] else []

    # Parse the detailed description if available
    detailed_description = (
        json.loads(product["detailed_description"]) if product["detailed_description"] else []
    )

    conn.close()

    return render_template(
        "product_detail.html",
        product=product,
        discounted_price=discounted_price,
        delivery_city=delivery_city,
        categories=categories,
        image_paths=image_paths,
        detailed_description=detailed_description,
    )




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM user WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']  # Store user_id in session
            session['user_email'] = user['email']
            session['user_name'] = user['first_name']  # Store user's first name
            return redirect('/')
        else:
            return render_template('login.html', error="Invalid email or password")
    return render_template('login.html')



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        age = request.form["age"]
        phone = request.form["phone"]
        password = request.form["password"]

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO user (first_name, last_name, email, age, phone, password) VALUES (?, ?, ?, ?, ?, ?)",
                         (first_name, last_name, email, age, phone, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Email already exists!"
        finally:
            conn.close()

        return redirect("/login")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/add_address", methods=["GET", "POST"])
def add_address():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        address_line_1 = request.form["address_line_1"]
        address_line_2 = request.form["address_line_2"]
        city = request.form["city"]
        state = request.form["state"]
        landmark = request.form["landmark"]
        pincode = request.form["pincode"]
        contact_number = request.form["contact_number"]

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO address (user_id, address_line_1, address_line_2, city, state, landmark, pincode, contact_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session["user_id"], address_line_1, address_line_2, city, state, landmark, pincode, contact_number))
        conn.commit()
        conn.close()

        return redirect("/")
    return render_template("address.html")

@app.route("/merchant_signup", methods=["GET", "POST"])
def merchant_signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone1 = request.form["phone1"]
        phone2 = request.form["phone2"]
        gstin = request.form["gstin"]
        address = request.form["address"]
        merchant_type = request.form["merchant_type"]
        password = request.form["password"]

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO merchant (name, email, phone1, phone2, gstin, address, merchant_type, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, email, phone1, phone2, gstin, address, merchant_type, password),
        )
        conn.commit()
        conn.close()
        return redirect("/merchant_login")
    return render_template("mer_signup.html")

@app.route("/merchant_login", methods=["GET", "POST"])
def merchant_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        merchant = conn.execute(
            "SELECT * FROM merchant WHERE email = ? AND password = ?", (email, password)
        ).fetchone()
        conn.close()

        if merchant:
            session["merchant_email"] = merchant["email"]
            return redirect("/merchant_dashboard")
        else:
            return "Invalid credentials!"
    return render_template("mer_login.html")

@app.route("/merchant_dashboard", methods=["GET", "POST"])
def merchant_dashboard():
    if "merchant_email" not in session:
        return redirect("/merchant_login")

    merchant_email = session["merchant_email"]
    conn = get_db_connection()

    # Fetch categories and subcategories for the dropdown
    categories = conn.execute("SELECT * FROM categories").fetchall()
    subcategories = conn.execute("SELECT * FROM subcategories").fetchall()

    # Handle status update from form submission
    if request.method == "POST":
        order_id = request.form.get("order_id")
        new_status = request.form.get("new_status")

        if order_id and new_status:
            conn.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (new_status, order_id),
            )
            conn.commit()
    merchant = conn.execute(
        "SELECT name FROM merchant WHERE email = ?", (merchant_email,)
    ).fetchone()

    if request.method == "POST":
        product_id = request.form.get("product_id")
        if product_id:
            name = request.form["name"]
            description = request.form["description"]
            price = float(request.form["price"])
            stock = int(request.form["stock"])
            discount = float(request.form.get("discount", 0))
            category_id = request.form["category"]
            subcategory_id = request.form["subcategory"]

            # Update the product details in the database
            conn.execute(
                """
                UPDATE product
                SET name = ?, description = ?, price = ?, stock = ?, discount = ?, category_id = ?, subcategory_id = ?
                WHERE id = ? AND email = ?
                """,
                (name, description, price, stock, discount, category_id, subcategory_id, product_id, session["merchant_email"]),
            )
            conn.commit()

    # Fetch the merchant's listed products, including category and subcategory
    products = conn.execute(
        """
        SELECT p.id, p.name, p.price, p.stock, p.approve, 
            c.name AS category_name, s.name AS subcategory_name 
        FROM product p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN subcategories s ON p.subcategory_id = s.id
        WHERE p.email = ?
        """, 
        (merchant_email,)
    ).fetchall()

    # Fetch additional metrics if needed
    total_sales = conn.execute(
        "SELECT COALESCE(SUM(o.price), 0) FROM orders o JOIN product p ON o.product_id = p.id WHERE p.email = ?",
        (merchant_email,)
    ).fetchone()[0]
    pending_orders = conn.execute(
        """
        
        SELECT o.id, o.product_id, o.purchaser, o.price, o.quantity, o.status, u.first_name AS purchaser_name, p.name AS product_name
        FROM orders o
        JOIN user u ON o.purchaser = u.id
        JOIN product p ON o.product_id = p.id
        WHERE p.email = ? AND o.status = 'accepted'
        """,
        (merchant_email,),
    ).fetchall()

    shipping_orders = conn.execute(
        """
        SELECT o.id, o.product_name, o.quantity, o.price, o.status, u.first_name AS purchaser_name
        FROM orders o
        JOIN product p ON o.product_id = p.id
        JOIN user u ON o.purchaser = u.id
        WHERE p.email = ? AND o.status = 'shipping'
        """,
        (merchant_email,),
    ).fetchall()

    shipped_orders = conn.execute(
        """
        SELECT o.id, o.product_name, o.quantity, o.price, o.status, u.first_name AS purchaser_name
        FROM orders o
        JOIN product p ON o.product_id = p.id
        JOIN user u ON o.purchaser = u.id
        WHERE p.email = ? AND o.status = 'Shipped'
        """,
        (merchant_email,),
    ).fetchall()

    pending_approvals = conn.execute(
        "SELECT COUNT(*) FROM orders o JOIN product p ON o.product_id = p.id WHERE p.email = ? AND o.status = '0'",
        (merchant_email,),
    ).fetchone()[0]

    listed_products = conn.execute(
        "SELECT COUNT(*) FROM product WHERE email = ?", (merchant_email,)
    ).fetchone()[0]
    
    total_products = conn.execute(
        "SELECT COUNT(*) FROM product WHERE email = ?", (merchant_email,)
    ).fetchone()[0]

    # Fetch active orders
    active_orders = conn.execute(
        """
        SELECT o.id, p.name AS product_name, o.quantity, 
               u.first_name || ' ' || u.last_name AS purchaser_name,
               addr.address_line_1 || ', ' || addr.city || ', ' || addr.state || ', ' || addr.pincode AS shipping_address
        FROM orders o
        JOIN product p ON o.product_id = p.id
        JOIN user u ON o.purchaser = u.id
        JOIN address addr ON o.shipping_address_id = addr.id
        WHERE p.email = ?
        """,
        (merchant_email,),
    ).fetchall()

    conn.close()

    return render_template(
        "merchant_dashboard.html",
        merchant_name=merchant['name'],
        products=products,
        categories=categories,
        subcategories=subcategories,
        total_sales=total_sales,
        pending_orders=pending_orders,
        shipping_orders=shipping_orders,
        shipped_orders=shipped_orders,
        listed_products=listed_products,
        pending_approvals=pending_approvals,
        active_orders=active_orders,
        total_products=total_products
    )

@app.route("/category/<int:category_id>")
def category_page(category_id):
    conn = get_db_connection()
    
    # Fetch category name
    category = conn.execute(
        "SELECT name FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    
    # Fetch products in this category
    products = conn.execute(
        "SELECT id, name, price, image FROM product WHERE category_id = ?", (category_id,)
    ).fetchall()
    
    # Debug: Print product images
    for product in products:
        print(f"Product ID {product['id']}, Image Path: {product['image']}")
    
    # Fetch all categories for dropdown
    categories = conn.execute("SELECT id, name FROM categories").fetchall()
    conn.close()

    return render_template(
        "category-page.html",
        category_name=category["name"] if category else "Unknown",
        products=products,
        categories=categories,
        delivery_city="Your City"  # Replace with dynamic user delivery city if available
    )


@app.route("/place_order", methods=["POST"])
def place_order():
    if "user_email" not in session:
        return redirect("/login")

    user_email = session["user_email"]
    conn = get_db_connection()

    # Fetch user's default address
    user_address = conn.execute(
        """
        SELECT id FROM address WHERE user_id = (
            SELECT id FROM user WHERE email = ?
        ) LIMIT 1
        """,
        (user_email,),
    ).fetchone()

    if not user_address:
        conn.close()
        return "No address found. Please add an address before placing an order."

    shipping_address_id = user_address["id"]

    # Retrieve cart details
    cart_items = conn.execute(
        """
        SELECT c.product_id, c.quantity, p.price, u.id AS user_id
        FROM cart c
        JOIN product p ON c.product_id = p.id
        JOIN user u ON u.email = ?
        WHERE c.user_email = ?
        """,
        (user_email, user_email),
    ).fetchall()

    # Insert orders into the orders table
    for item in cart_items:
        conn.execute(
            """
            INSERT INTO orders (product_id, quantity, price, purchaser, shipping_address_id, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (
                item["product_id"],
                item["quantity"],
                item["price"],
                item["user_id"],
                shipping_address_id,
            ),
        )

    # Clear the cart
    conn.execute("DELETE FROM cart WHERE user_email = ?", (user_email,))
    conn.commit()
    conn.close()

    return redirect("/your_orders")

@app.route("/add_product", methods=["POST"])
def add_product():
    if "merchant_email" not in session:
        return redirect("/merchant_login")

    # Collect product details
    name = request.form["name"]
    description = request.form["description"]
    price = float(request.form["price"])
    stock = int(request.form["stock"])
    discount = float(request.form.get("discount", 0))
    category_id = request.form.get("category_id")  # Category ID
    subcategory_id = request.form.get("subcategory_id")  # Subcategory ID

    # Handle multiple images
    images = request.files.getlist("images")
    if len(images) > 7:
        return "You can upload a maximum of 7 images.", 400  # Restrict to 7 images

    # Save images to static/images directory and store paths
    image_paths = []
    for index, image in enumerate(images):
        image_path = f"static/images/{name.replace(' ', '_')}_{index+1}_{image.filename}"
        image.save(image_path)
        image_paths.append(image_path)

    # Join image paths into a comma-separated string
    image_paths_str = ",".join(image_paths)

    # Process the detailed description dynamically
    features = request.form.getlist("feature[]")
    details = request.form.getlist("detail[]")
    detailed_description = [{"feature": f, "detail": d} for f, d in zip(features, details)]

    # Insert product data into the database
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO product (email, name, description, detailed_description, price, stock, discount, image, category_id, subcategory_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["merchant_email"],
            name,
            description,
            json.dumps(detailed_description),  # Store detailed description as JSON
            price,
            stock,
            discount,
            image_paths_str,  # Comma-separated image paths
            category_id,
            subcategory_id,
        ),
    )
    conn.commit()
    conn.close()

    return redirect("/merchant_dashboard")



@app.route("/cancel_order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if "merchant_email" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    conn.execute("DELETE FROM active_order WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Order cancelled successfully"}), 200


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "user_email" not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    product_id = data.get("product_id")
    user_email = session["user_email"]

    conn = get_db_connection()

    # Get user ID from email
    user = conn.execute("SELECT id FROM user WHERE email = ?", (user_email,)).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = user["id"]

    # Check if the product is already in the cart
    existing_cart_item = conn.execute(
        "SELECT * FROM cart WHERE user_id = ? AND product_id = ?",
        (user_id, product_id),
    ).fetchone()

    if existing_cart_item:
        # Increment quantity if the product is already in the cart
        conn.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE id = ?",
            (existing_cart_item["id"],),
        )
    else:
        # Add new item to the cart
        conn.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (user_id, product_id, 1),
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Product added to cart!"}), 200



@app.route("/cart")
def cart():
    if "user_email" not in session:
        return redirect("/login")

    conn = get_db_connection()
    first_name = None
    selected_city = None

    if "user_id" in session:
        user = conn.execute("SELECT first_name FROM user WHERE id = ?", (session["user_id"],)).fetchone()
        first_name = user["first_name"] if user else None

        # Fetch the user's default or first address
        address = conn.execute("SELECT city FROM address WHERE user_id = ? LIMIT 1", (session["user_id"],)).fetchone()
        selected_city = address["city"] if address else None

    # Get the user ID based on session email
    user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user_email"],)).fetchone()

    # Fetch cart items for the user
    cart_items = conn.execute(
        """
        SELECT c.id AS cart_id, p.id AS product_id, p.name, p.price, p.discount, p.image, c.quantity
        FROM cart c
        JOIN product p ON c.product_id = p.id
        WHERE c.user_id = ?
        """,
        (user["id"],),
    ).fetchall()

    conn.close()

    return render_template("cart.html", cart_items=cart_items,first_name=first_name, selected_city=selected_city)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    data = request.get_json()
    product_id = data.get('product_id')  # Use product_id here instead of product_name
    quantity = data.get('quantity')

    if not product_id or not quantity:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    try:
        conn = get_db_connection()

        # Update the cart with the new quantity
        conn.execute("""
            UPDATE cart
            SET quantity = ?
            WHERE user_id = ? AND product_id = ?
        """, (quantity, session['user_id'], product_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating cart: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500

@app.route("/remove_from_cart/<int:cart_id>")
def remove_from_cart(cart_id):
    if "user_email" not in session:
        return redirect("/login")

    conn = get_db_connection()
    conn.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    conn.commit()
    conn.close()

    return redirect("/cart")


@app.route("/clear_cart")
def clear_cart():
    if "user_email" not in session:
        return redirect("/login")

    conn = get_db_connection()

    # Get the user ID based on session email
    user = conn.execute("SELECT id FROM user WHERE email = ?", (session["user_email"],)).fetchone()

    # Clear cart items for the user
    conn.execute("DELETE FROM cart WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()

    return redirect("/cart")



@app.route("/delivery_signup", methods=["GET", "POST"])
def delivery_signup():
    if request.method == "POST":
        name = request.form["name"]
        state = request.form["state"]
        city = request.form["city"]
        age = request.form["age"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        license = request.files["license"]

        # Define the directory and file path for the license
        license_dir = "static/licenses"
        license_path = os.path.join(license_dir, f"{email}_license.jpg")

        # Ensure the directory exists
        if not os.path.exists(license_dir):
            os.makedirs(license_dir)

        # Save the uploaded license file
        license.save(license_path)

        conn = get_db_connection()

        # Insert delivery partner data into the database
        try:
            conn.execute(
                """
                INSERT INTO delivery (name, state, city, age, email, phone, password, license_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, state, city, age, email, phone, password, license_path),
            )
            conn.commit()
        except Exception as e:
            conn.close()
            return f"Error: {e}", 400

        conn.close()
        return redirect("/delivery_login")

    return render_template("delivery_signup.html")


@app.route("/delivery_login", methods=["GET", "POST"])
def delivery_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        delivery_partner = conn.execute(
            "SELECT id, password, approved FROM delivery WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if delivery_partner:
            if delivery_partner["password"] == password:
                session["delivery_id"] = delivery_partner["id"]  # Set session

                # Redirect to delivery dashboard
                return redirect("/delivery_dashboard")
            else:
                return render_template(
                    "delivery_login.html", error="Incorrect password."
                )
        else:
            return render_template(
                "delivery_login.html", error="Account not found. Please sign up."
            )

    return render_template("delivery_login.html")



@app.route("/delivery_logout")
def delivery_logout():
    session.pop("delivery_email", None)
    return redirect("/delivery_login")


@app.route("/delivery_dashboard")
def delivery_dashboard():
    if "delivery_id" not in session:
        return redirect("/delivery_login")
    
    delivery_id = session["delivery_id"]
    conn = get_db_connection()

    # Fetch delivery partner details
    delivery_partner = conn.execute(
        "SELECT * FROM delivery WHERE id = ?", (delivery_id,)
    ).fetchone()

    if not delivery_partner:
        return "Delivery partner not found", 404

    # Initialize orders and history
    active_orders = []
    order_history = []

    # Update order status to "delivered" if requested
    if request.method == "POST":
        order_id = request.form.get("order_id")
        image = request.files.get("delivery_image")
        if order_id and image:
            image_path = f"static/delivery_images/{order_id}_delivered.jpg"
            image.save(image_path)

            conn.execute(
                "UPDATE orders SET status = 'delivered', delivery_image = ?, delivery_partner_id = ? WHERE id = ?",
                (image_path, delivery_id, order_id),
            )
            conn.commit()

    approved = delivery_partner["approved"]
    city = delivery_partner["city"]
    
    # Fetch active orders (status = "shipping") assigned to this delivery partner
    if approved == 1:
        active_orders = conn.execute("""
            SELECT o.id AS order_id, p.name AS product_name, 
                   m.address AS merchant_address, m.phone1 AS merchant_contact,
                   a.address_line_1 || ', ' || a.address_line_2 || ', ' || a.city || ', ' || a.state || ' - ' || a.pincode || ' (Landmark: ' || a.landmark || ')' AS purchaser_address,
                   a.contact_number AS purchaser_contact, o.status AS status
            FROM orders o
            JOIN product p ON o.product_id = p.id
            JOIN merchant m ON p.email = m.email
            JOIN address a ON o.shipping_address_id = a.id
            WHERE o.status = 'Shipped' AND a.city = ? AND o.delivery_partner_id = ?
        """, (city, delivery_id)).fetchall()

    # Fetch order history (status = "delivered") assigned to this delivery partner
    order_history = conn.execute("""
        SELECT o.id, o.product_id, o.quantity, o.price, o.status,
               u.first_name AS purchaser_name,
               a.state, a.city, a.pincode,
               p.name AS product_name, o.delivery_image
        FROM orders o
        JOIN user u ON o.purchaser = u.id
        JOIN address a ON o.shipping_address_id = a.id
        JOIN product p ON o.product_id = p.id
        WHERE o.status = 'delivered' AND o.delivery_partner_id = ?
    """, (delivery_id,)).fetchall()

    conn.close()

    return render_template(
        "delivery_dashboard.html",
        delivery_partner=delivery_partner,
        active_orders=active_orders,
        order_history=order_history
    )


@app.route('/update_stock', methods=['POST'])
def update_stock():
    if 'user_id' not in session:
        return redirect('/merchant_login')

    data = request.get_json()
    product_id = data.get('product_id')
    additional_stock = data.get('additional_stock')

    conn = get_db_connection()
    try:
        conn.execute("""
            UPDATE product
            SET stock = stock + ?
            WHERE id = ?
        """, (additional_stock, product_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Stock updated successfully'})
    except Exception as e:
        print(f"Error updating stock: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500
    finally:
        conn.close()


@app.route('/mark_delivered/<int:order_id>', methods=['POST'])
def mark_delivered(order_id):
    if "delivery_id" not in session:
        return redirect("/delivery_login")

    delivery_id = session["delivery_id"]
    conn = get_db_connection()

    # Retrieve the delivery image and save it
    image = request.files.get("delivery_image")
    if image:
        image_path = f"static/delivery_images/{order_id}_delivered.jpg"
        image.save(image_path)

        # Update the order status and save the image path in the database
        conn.execute(
            "UPDATE orders SET status = 'delivered', delivery_image = ? WHERE id = ?",
            (image_path, order_id),
        )
        conn.commit()

    conn.close()

    return redirect("/delivery_dashboard") 


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        
        # Check if admin exists in the database
        admin = conn.execute(
            "SELECT * FROM admin WHERE email = ? AND password = ?", 
            (email, password)
        ).fetchone()
        conn.close()

        if admin:
            session['admin_email'] = admin['email']
            session['admin_name'] = admin['name']  # Store admin name in session
            return redirect('/admin_panel')
        else:
            return render_template('admin_login.html', error="Invalid login credentials")
    
    return render_template('admin_login.html')

@app.route('/admin_panel')
def admin_dashboard():
    if 'admin_email' not in session:
        return redirect('/admin_login')

    conn = get_db_connection()

    # Fetch products pending approval
    pending_approval = conn.execute(
    """
        SELECT p.id, p.name, p.description, p.price, p.stock, p.image, 
            c.name AS category_name, s.name AS subcategory_name, 
            m.name AS merchant_name 
        FROM product p 
        JOIN merchant m ON p.email = m.email
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN subcategories s ON p.subcategory_id = s.id
        WHERE p.approve = 0
        """
    ).fetchall()

    delivery_partners = conn.execute('SELECT * FROM delivery').fetchall()
    conn.close()

    conn.close()
    conn.close()

    return render_template(
        'admin_panel.html',
        admin_name=session['admin_name'],
        pending_approval=pending_approval,
        delivery_partners=delivery_partners,
    )

@app.route('/approve_product/<int:product_id>', methods=['POST'])
def approve_product(product_id):
    if 'admin_email' not in session:
        return redirect('/admin_login')

    conn = get_db_connection()
    conn.execute("UPDATE product SET approve = 1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect('/admin_panel')


@app.route('/reject_product/<int:product_id>', methods=['POST'])
def reject_product(product_id):
    if 'admin_email' not in session:
        return redirect('/admin_login')

    conn = get_db_connection()
    conn.execute("UPDATE product SET approve = -1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect('/admin_panel')


@app.route('/approve_delivery_partner/<int:delivery_partner_id>', methods=['POST'])
def approve_delivery_partner(delivery_partner_id):
    conn = get_db_connection()
    conn.execute('UPDATE delivery SET approved = 1 WHERE id = ?', (delivery_partner_id,))
    conn.commit()
    conn.close()
    return redirect('/admin_panel')  # Redirect to the admin panel after approval

@app.route('/deny_delivery_partner/<int:delivery_partner_id>', methods=['POST'])
def deny_delivery_partner(delivery_partner_id):
    conn = get_db_connection()
    conn.execute('UPDATE delivery SET approved = -1 WHERE id = ?', (delivery_partner_id,))
    conn.commit()
    conn.close()
    return redirect('/admin_panel')  # Redirect to the admin panel after denial


def payment_success():
    if 'user_email' not in session:
        return redirect('/login')
    
    user_email = session['user_email']
    conn = get_db_connection()

    # Fetch user ID
    user = conn.execute("SELECT id FROM user WHERE email = ?", (user_email,)).fetchone()
    user_id = user['id']

    # Fetch items in cart
    cart_items = conn.execute(
        "SELECT product_name, price FROM cart WHERE user_email = ?",
        (user_email,)
    ).fetchall()

    # Add each cart item to orders
    for item in cart_items:
        conn.execute(
            "INSERT INTO orders (product_name, price, purchaser, shipping_address) "
            "VALUES (?, ?, ?, ?)",
            (item['product_name'], item['price'], user_id, user_email)
        )

    # Clear the user's cart
    conn.execute("DELETE FROM cart WHERE user_email = ?", (user_email,))
    conn.commit()
    conn.close()

    return redirect('/your_orders')

@app.route('/your_orders')
def your_orders():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()

    # Fetch orders with the required details
    orders = conn.execute("""
        SELECT 
            o.id AS order_id,
            p.name AS product_name,
            o.quantity AS quantity,
            o.price AS price,
            o.status AS status,
            a.city AS city,
            a.address_line_1 || ', ' || a.address_line_2 || ', ' || a.city || ', ' || a.state AS shipping_address,
            d.name AS delivery_partner_name
        FROM orders o
        JOIN product p ON o.product_id = p.id
        JOIN address a ON o.shipping_address_id = a.id
        LEFT JOIN delivery d ON o.delivery_partner_id = d.id
        WHERE o.purchaser = ?
    """, (user_id,)).fetchall()

    first_name = None
    selected_city = None

    # Fetch user details and selected city
    if "user_id" in session:
        user = conn.execute("SELECT first_name FROM user WHERE id = ?", (session["user_id"],)).fetchone()
        first_name = user["first_name"] if user else None

        address = conn.execute("SELECT city FROM address WHERE user_id = ? LIMIT 1", (session["user_id"],)).fetchone()
        selected_city = address["city"] if address else None

    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()

    # Render the template with the retrieved data
    return render_template(
        'your_orders.html',
        orders=orders,
        first_name=first_name,
        categories=categories,
        selected_city=selected_city
    )


@app.route('/checkout', methods=['GET'])
def checkout():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()

    # Retrieve cart items with correct quantities
    cart_items = conn.execute("""
        SELECT cart.product_id, cart.quantity, product.name AS product_name, product.price, product.stock
        FROM cart
        JOIN product ON cart.product_id = product.id
        WHERE cart.user_id = ?
    """, (user_id,)).fetchall()

    conn.close()

    return render_template('checkout.html', cart_items=cart_items)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    conn = get_db_connection()

    # Retrieve the city from the cart session
    address = conn.execute(
        "SELECT city FROM address WHERE user_id = ? LIMIT 1",
        (user_id,)
    ).fetchone()
    selected_city = address["city"] if address else None

    if not selected_city:
        conn.close()
        return "No city selected for the order", 400

    # Retrieve cart items for the user
    cart_items = conn.execute(
        """
        SELECT c.product_id, c.quantity, p.price, p.name, p.stock
        FROM cart c
        JOIN product p ON c.product_id = p.id
        WHERE c.user_id = ?
        """,
        (user_id,),
    ).fetchall()

    if not cart_items:
        conn.close()
        return "No items in the cart", 400

    # Retrieve user's address ID for shipping
    user_address = conn.execute(
        "SELECT id FROM address WHERE user_id = ? AND city = ? LIMIT 1",
        (user_id, selected_city),
    ).fetchone()

    if not user_address:
        conn.close()
        return "No shipping address found for the selected city", 400

    address_id = user_address["id"]

    # Assign delivery partner or queue order
    for item in cart_items:
        if item["quantity"] > item["stock"]:
            conn.close()
            return f"Not enough stock for product: {item['name']}", 400

        delivery_partner = conn.execute(
            """
            SELECT id
            FROM delivery
            WHERE approved = 1 AND city = ?
            AND id NOT IN (
                SELECT delivery_partner_id FROM orders WHERE status NOT IN ('delivered', 'cancelled')
            )
            LIMIT 1
            """,
            (selected_city,),
        ).fetchone()

        delivery_partner_id = delivery_partner["id"] if delivery_partner else None

        # Insert the order into the database
        conn.execute(
            """
            INSERT INTO orders (
                product_id, purchaser, price, product_name, quantity, shipping_address_id, city, status, delivery_partner_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["product_id"],
                user_id,
                item["price"],
                item["name"],
                item["quantity"],
                address_id,
                selected_city,
                "accepted" if delivery_partner_id else "queued",
                delivery_partner_id,
            ),
        )

        # Reduce the stock of the product after the order is placed
        conn.execute(
            """
            UPDATE product
            SET stock = stock - ?
            WHERE id = ?
            """,
            (item["quantity"], item["product_id"]),
        )

    # Clear the cart after order placement
    conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return redirect("/your_orders")

@app.route('/support_login', methods=['GET', 'POST'])
def support_login():
    if request.method == 'GET':
        # Render the login page
        return render_template('support_login.html')

    # Handle login form submission
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    user = conn.execute("""
        SELECT * FROM support_staff WHERE username = ? AND password = ?
    """, (username, password)).fetchone()
    conn.close()

    if user:
        session['support_id'] = user['id']
        return redirect('/support_dashboard')

    # Invalid credentials
    return render_template('support_login.html', error="Invalid username or password")


@app.route('/support_dashboard', methods=['GET'])
def support_dashboard():
    if 'support_id' not in session:
        return redirect('/support_login')

    conn = get_db_connection()
    grievances = conn.execute("""
        SELECT o.id AS order_id, o.grievance_reason AS reason, o.grievance_status AS status,
               u.first_name AS user_name, p.name AS product_name, p.price AS product_price
        FROM orders o
        JOIN user u ON o.user_id = u.id
        JOIN product p ON o.product_id = p.id
        WHERE o.grievance_status != 'resolved'
    """).fetchall()
    conn.close()

    return render_template('support_dashboard.html', grievances=grievances)

@app.route('/support_logout')
def support_logout():
    session.pop('support_id', None)
    return redirect('/support_login')


@app.route('/initiate_grievance', methods=['POST'])
def initiate_grievance():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    order_id = data['order_id']
    grievance_reason = data['reason']

    conn = get_db_connection()
    conn.execute("""
        UPDATE orders 
        SET grievance_reason = ?, grievance_status = 'open' 
        WHERE id = ? AND user_id = ?
    """, (grievance_reason, order_id, session['user_id']))
    conn.commit()

    # Add initial grievance message
    conn.execute("""
        INSERT INTO chats (user_id, order_id, message, sender)
        VALUES (?, ?, ?, 'user')
    """, (session['user_id'], order_id, grievance_reason))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/support_chats/<int:order_id>', methods=['GET'])
def support_chats(order_id):
    conn = get_db_connection()
    chats = conn.execute("""
        SELECT message, sender, timestamp
        FROM chats
        WHERE order_id = ?
        ORDER BY timestamp ASC
    """, (order_id,)).fetchall()
    conn.close()

    return jsonify([dict(chat) for chat in chats])

@app.route('/support_reply', methods=['POST'])
def support_reply():
    data = request.json
    order_id = data['order_id']
    message = data['message']

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO chats (user_id, order_id, message, sender)
        VALUES (NULL, ?, ?, 'support')
    """, (order_id, message))
    conn.commit()
    conn.close()

    return jsonify({'success': True})



@app.route('/order_grievance/<int:order_id>', methods=['GET'])
def order_grievance(order_id):
    if 'user_id' not in session:
        return redirect('/user_login')

    conn = get_db_connection()
    order = conn.execute("""
        SELECT o.id, o.product_name, o.price, o.merchant_name, o.delivery_partner_name, o.delivery_date
        FROM orders o
        WHERE o.id = ? AND o.user_id = ?
    """, (order_id, session['user_id'])).fetchone()

    conn.close()
    if not order:
        return "Order not found", 404

    return render_template('order_grievance.html', order=order)


@app.route('/fetch_chats/<int:order_id>', methods=['GET'])
def fetch_chats(order_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_connection()
    chats = conn.execute("""
        SELECT message, sender, timestamp 
        FROM chats 
        WHERE order_id = ?
        ORDER BY timestamp ASC
    """, (order_id,)).fetchall()
    conn.close()

    return jsonify([dict(chat) for chat in chats])

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    user_id = session['user_id']
    order_id = data['order_id']
    message = data['message']

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO chats (user_id, order_id, message, sender)
        VALUES (?, ?, ?, 'user')
    """, (user_id, order_id, message))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# Add routes for address, merchant signup/login, admin, cart, orders, etc.

if __name__ == "__main__":
    app.run(debug=True)
