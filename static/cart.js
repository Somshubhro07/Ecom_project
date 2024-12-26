document.addEventListener("DOMContentLoaded", () => {
    updateSubtotal();

    // Add event listeners for quantity changes
    document.querySelectorAll(".quantity-input").forEach((input) => {
        input.addEventListener("change", (event) => {
            const row = event.target.closest("tr");
            const price = parseFloat(row.querySelector(".price").textContent.replace("₹", ""));
            const quantity = parseInt(event.target.value);
            const productId = event.target.getAttribute("data-product-id");  // Get product_id from data attribute

            // Update the total for the specific row
            const totalCell = row.querySelector(".total");
            if (totalCell) {
                totalCell.textContent = `₹${(price * quantity).toFixed(2)}`;
            }

            updateSubtotal();

            // Update the quantity in the database
            updateQuantityInDatabase(productId, quantity);  // Send product_id instead of product_name
        });
    });


    // Add event listeners for remove buttons
    document.querySelectorAll(".remove-item").forEach((button) => {
        button.addEventListener("click", (event) => {
            const cartId = event.target.getAttribute("data-cart-id");
            removeItemFromCart(cartId);
        });
    });

    // Add event listener for clearing the cart
    const clearCartButton = document.getElementById("clear-cart");
    if (clearCartButton) {
        clearCartButton.addEventListener("click", clearCart);
    }
});

// Function to update the subtotal dynamically
function updateSubtotal() {
    let subtotal = 0;
    document.querySelectorAll("tbody tr").forEach((row) => {
        const price = parseFloat(row.querySelector(".price").textContent.replace("₹", ""));
        const quantity = parseInt(row.querySelector(".quantity-input").value);
        subtotal += price * quantity;
    });

    const subtotalElement = document.getElementById("subtotal");
    if (subtotalElement) {
        subtotalElement.textContent = subtotal.toFixed(2);
    }
}

// Function to update quantity in the database
function updateQuantityInDatabase(productId, quantity) {
    fetch("/update_cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            product_id: productId,  // Send product_id here
            quantity: quantity
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (!data.success) {
                alert(data.message || "Could not update the quantity. Please try again.");
            }
        })
        .catch((error) => {
            console.error("Error updating quantity in the database:", error);
            alert("Something went wrong. Please try again.");
        });
}

// Function to remove an item from the cart
function removeItemFromCart(cartId) {
    fetch(`/remove_from_cart/${cartId}`, {
        method: "GET",
    })
        .then((response) => {
            if (response.ok) {
                showMessage("Item has been removed from the cart.", "success");
                window.location.reload();
            } else {
                showMessage("Failed to remove item from cart.", "error");
            }
        })
        .catch((error) => {
            console.error("Error removing item from cart:", error);
            showMessage("Something went wrong. Please try again.", "error");
        });
}

// Function to display custom messages
function showMessage(message, type) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;

    // Append to the body and auto-remove after 3 seconds
    document.body.appendChild(messageDiv);
    setTimeout(() => {
        document.body.removeChild(messageDiv);
    }, 3000);
}

// Function to clear the entire cart
function clearCart() {
    fetch("/clear_cart", {
        method: "GET",
    })
        .then((response) => {
            if (response.ok) {
                // Reload the page to reflect the updated cart
                window.location.reload();
            } else {
                alert("Failed to clear the cart.");
            }
        })
        .catch((error) => {
            console.error("Error clearing the cart:", error);
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const checkoutButton = document.getElementById("checkout-btn");

    // Function to handle checkout button click
    function handleCheckout() {
        // Redirect to the checkout summary page
        window.location.href = "/checkout";
    }

    // Attach event listener to the checkout button
    checkoutButton.addEventListener("click", handleCheckout);
});
