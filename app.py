from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import pandas as pd
import matplotlib.pyplot as plt
import shutil
import uuid

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

# Ensure folders exist
for folder in [UPLOAD_FOLDER, STATIC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Utility function: allowed file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Utility function: clear folder
def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove file or symbolic link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directory
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# Upload Route
@app.route('/upload', methods=['POST'])
def upload_file():
    clear_folder(UPLOAD_FOLDER)  # Clear previous uploads
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = "uploaded_file.csv"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('index'))
    else:
        return "Invalid file format. Please upload a CSV file."

# Preprocess Route
@app.route('/preprocess', methods=['POST'])
def preprocess_file():
    try:
        file_path = os.path.join(UPLOAD_FOLDER, "uploaded_file.csv")
        df = pd.read_csv(file_path)

        # Preprocessing: Remove null values
        df = df.dropna()

        # Optional: Reset index
        df = df.reset_index(drop=True)

        # Save preprocessed file (overwriting previous)
        df.to_csv(file_path, index=False)
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error during preprocessing: {str(e)}"

# Generate General Report
@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        clear_folder(STATIC_FOLDER)  # Clear previous graphs

        file_path = os.path.join(UPLOAD_FOLDER, "uploaded_file.csv")
        df = pd.read_csv(file_path)

        # Check if 'Status' column exists
        if 'Status' in df.columns:
            status_counts = df['Status'].value_counts()
            fig, ax = plt.subplots()
            ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=140)
            ax.set_title('Flight Status Distribution')
        else:
            # Fallback: if no 'Status' column, just plot number of records per Airline
            if 'Airline' in df.columns:
                airline_counts = df['Airline'].value_counts()
                fig, ax = plt.subplots()
                airline_counts.plot(kind='bar', ax=ax, color='skyblue')
                ax.set_ylabel('Number of Flights')
                ax.set_xlabel('Airline')
                ax.set_title('Flights per Airline')
            else:
                # Fallback if even 'Airline' missing: Just empty plot
                fig, ax = plt.subplots()
                ax.text(0.5, 0.5, 'No Suitable Columns for Graph', 
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=12, color='red')
                ax.axis('off')

        # Save the graph
        graph_id = str(uuid.uuid4()) + ".png"
        graph_path = os.path.join(STATIC_FOLDER, graph_id)
        plt.tight_layout()
        plt.savefig(graph_path)
        plt.close()

        # Pass DataFrame to HTML
        table_html = df.head(50).to_html(classes='table table-striped', index=False)

        return render_template('report.html', tables=table_html, graph_url=url_for('static', filename=graph_id))

    except Exception as e:
        return f"Error during report generation: {str(e)}"


# Generate Flight-Specific Report
@app.route('/generate_flight_report', methods=['POST'])
def generate_flight_report():
    try:
        flight_number = request.form.get('flight_number')
        file_path = os.path.join(UPLOAD_FOLDER, "uploaded_file.csv")
        df = pd.read_csv(file_path)

        # Filter DataFrame for specific flight number
        flight_df = df[df['FlightNumber'] == flight_number]

        if flight_df.empty:
            return f"No data found for Flight Number: {flight_number}"

        # Pass DataFrame to HTML
        table_html = flight_df.to_html(classes='table table-striped', index=False)

        return render_template('flight_report.html', tables=table_html, flight_number=flight_number)

    except Exception as e:
        return f"Error during flight report generation: {str(e)}"

# Run the Flask App
if __name__ == "__main__":
    app.run(debug=True)
