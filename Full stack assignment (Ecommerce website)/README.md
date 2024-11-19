# ecom-fullstack-assignment

# E-Commerce Platform Using Flask

This is a simple e-commerce platform built using Flask. It allows users to register, login, and 
perform basic operations such as adding products to their carts and making purchases.

## Prerequisites

Before running the project, make sure you have Python installed on your system. You can download it 
from [Python's official website](https://www.python.org/downloads/).

Additionally, ensure that SQLite is installed on your system. It comes bundled with Python by 
default but if it's not installed, you can install it using pip:

```sh
pip install sqlite3
```

## Installation

1. Clone the repository to your local machine:

    ```sh
    git clone https://github.com/yourusername/ecommerce-platform.git
    cd ecommerce-platform
    ```

2. Install the required Python packages using pip:

    ```sh
    pip install -r requirements.txt
    ```

3. Create a SQLite database and replace `ecommerce.db` with your desired database name in the `init_
db()` function in `app.py`.

## Running the Application

1. Run the application by executing the following command in the terminal:

    ```sh
    python app.py
    ```

2. Open your web browser and navigate to `http://127.0.0.1:5000/`. You should see a login page 
where you can create an account or log in with an existing one.

## Features

- **User Registration**: Users can register by providing their username, email, password, and user 
type (admin or seller).
- **Login**: Users can log in using their credentials. After logging in, they are redirected to 
their dashboard based on their user type.
- **Product Management**: Admins have access to manage regular products and seller products 
separately. They can add new products, edit existing ones, and remove them from the platform.
- **Cart Management**: Users can add items to their cart, view the cart contents, and proceed to 
checkout.
- **Order Management**: Once a user is logged in, they can place orders for the products in their 
cart.

## To Do

1. Add more security measures such as password hashing, CSRF protection, session management, and 
API documentation.
2. Implement multi-factor authentication.
3. Add support for payment gateways.
4. Improve user experience by adding animations, improving responsiveness, and optimizing database 
queries.

This is a basic implementation of an e-commerce platform using Flask. It can be expanded with more 
features and security measures as per the requirements.
