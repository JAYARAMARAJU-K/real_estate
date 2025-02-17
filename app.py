from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import pdfkit
import boto3
from botocore.exceptions import NoCredentialsError

app = Flask(__name__, template_folder="templates")
app.secret_key = "your_secret_key"

# SQLite Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///realestate.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# AWS S3 Configuration
S3_BUCKET = "your-s3-bucket-name"
S3_ACCESS_KEY = "your-access-key"
S3_SECRET_KEY = "your-secret-key"
S3_REGION = "your-region"

s3 = boto3.client(
    "s3",
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

# Helper function to upload file to S3
def upload_to_s3(file_path, bucket_name, s3_file_path):
    try:
        s3.upload_file(file_path, bucket_name, s3_file_path)
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

# Add Property Route (Modified)
@app.route("/add_property", methods=["POST"])
def add_property():
    try:
        if "user_id" not in session:
            return jsonify({"message": "Unauthorized"}), 403

        title = request.form["title"]
        property_type = request.form["type"]
        price = request.form["price"]
        bhk = request.form["bhk"]
        area = request.form["area"]
        location = request.form["location"]
        contact = request.form["contact"]
        description = request.form["description"]
        image = request.files["image"]

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(image_path)
            upload_to_s3(image_path, S3_BUCKET, f"uploads/{filename}")
        else:
            filename = None

        new_property = Property(
            title=title,
            property_type=property_type,
            price=price,
            bhk=bhk,
            area=area,
            location=location,
            contact=contact,
            description=description,
            image=filename,
            user_id=session["user_id"]
        )
        db.session.add(new_property)
        db.session.commit()

        flash("Property added successfully!", "success")
        return jsonify({"message": "Property added successfully!"})  # Return JSON response
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Internal Server Error"}), 500

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
