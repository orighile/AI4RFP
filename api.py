from flask import Flask, request, jsonify
import os
import sys
import json
import logging
from werkzeug.utils import secure_filename

# Add parent directory to path to import agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the AI RFP Agent
from agent import AiRfpAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Initialize the AI RFP Agent
agent = AiRfpAgent()

# Configure upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure allowed extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "AI RFP Agent API is running"}), 200

@app.route('/api/rfp/upload', methods=['POST'])
def upload_rfp():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Generate a unique RFP ID
        rfp_id = f"RFP-{filename.split('.')[0]}-{os.path.getmtime(file_path)}"
        
        return jsonify({
            "id": rfp_id,
            "filename": filename,
            "status": "uploaded",
            "file_path": file_path
        }), 201
    
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/api/rfp/<rfp_id>/analyze', methods=['POST'])
def analyze_rfp(rfp_id):
    # Get the file path from the request or database
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    try:
        # Initialize the input processor and RFP analyzer
        processed_text = agent.input_processor.process_document(file_path=file_path)
        rfp_analysis_data = agent.rfp_analyzer.extract_key_information(rfp_text_content=processed_text)
        rfp_analysis_data["rfp_id"] = rfp_id
        
        return jsonify({
            "id": rfp_id,
            "status": "analyzed",
            "analysis": rfp_analysis_data
        }), 200
    except Exception as e:
        logging.error(f"Error analyzing RFP: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/proposal/generate', methods=['POST'])
def generate_proposal():
    data = request.json
    rfp_id = data.get('rfpId')
    title = data.get('title')
    file_path = data.get('file_path')
    settings = data.get('settings', {})
    
    if not rfp_id or not title or not file_path:
        return jsonify({"error": "Missing required parameters"}), 400
    
    if not os.path.exists(file_path):
        return jsonify({"error": "RFP file not found"}), 404
    
    try:
        # Process the RFP and generate a proposal
        output_file_paths = agent.process_rfp(file_path, rfp_id, title)
        
        if not output_file_paths:
            return jsonify({"error": "Failed to generate proposal"}), 500
        
        proposal_id = f"PROP-{rfp_id}-{int(os.path.getmtime(output_file_paths.get('markdown_proposal', '')))}"
        
        return jsonify({
            "id": proposal_id,
            "title": title,
            "rfpId": rfp_id,
            "status": "in_progress",
            "output_files": output_file_paths
        }), 201
    except Exception as e:
        logging.error(f"Error generating proposal: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/proposal/<proposal_id>/status', methods=['GET'])
def get_proposal_status(proposal_id):
    # In a real implementation, this would check the actual status
    # For now, we'll simulate a status check
    return jsonify({
        "id": proposal_id,
        "status": "completed",
        "progress": 100,
        "message": "Proposal generation completed successfully"
    }), 200

@app.route('/api/proposal/<proposal_id>', methods=['GET'])
def get_proposal(proposal_id):
    # Extract RFP ID from proposal ID
    parts = proposal_id.split('-')
    if len(parts) < 2:
        return jsonify({"error": "Invalid proposal ID format"}), 400
    
    rfp_id = '-'.join(parts[1:-1])
    
    # In a real implementation, this would retrieve the proposal from storage
    # For now, we'll look for the most recent proposal file
    proposals_dir = './generated_proposals'
    
    try:
        # Find the markdown proposal file
        proposal_files = [f for f in os.listdir(proposals_dir) if f.endswith('.md')]
        if not proposal_files:
            return jsonify({"error": "Proposal not found"}), 404
        
        # Sort by modification time (newest first)
        proposal_files.sort(key=lambda f: os.path.getmtime(os.path.join(proposals_dir, f)), reverse=True)
        latest_proposal = proposal_files[0]
        
        with open(os.path.join(proposals_dir, latest_proposal), 'r') as f:
            content = f.read()
        
        # Parse the content into sections (simplified)
        sections = {
            "executive_summary": "Executive Summary section of the proposal",
            "technical_approach": "Technical Approach section of the proposal",
            "implementation_timeline": "Implementation Timeline section of the proposal",
            "team_qualifications": "Team Qualifications section of the proposal",
            "cost_proposal": "Cost Proposal section of the proposal"
        }
        
        return jsonify({
            "id": proposal_id,
            "title": latest_proposal.replace('.md', ''),
            "rfpId": rfp_id,
            "status": "completed",
            "content": sections,
            "file_path": os.path.join(proposals_dir, latest_proposal)
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving proposal: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/knowledge', methods=['GET'])
def search_knowledge():
    query = request.args.get('query', '')
    category = request.args.get('category', 'all')
    
    try:
        # Search the knowledge base
        results = []
        
        # Read insights file
        insights_file = os.path.join('./knowledge_base_data', 'rfp_insights.json')
        if os.path.exists(insights_file):
            with open(insights_file, 'r') as f:
                insights = json.load(f)
                for insight in insights:
                    if query.lower() in insight.get('content', '').lower() or not query:
                        if category == 'all' or category == 'rfp_insights':
                            results.append({
                                "id": insight.get('id', ''),
                                "title": insight.get('insight_type', ''),
                                "content": insight.get('content', ''),
                                "category": "rfp_insights",
                                "keywords": insight.get('keywords', []),
                                "date": insight.get('timestamp', '')
                            })
        
        # Read best practices file
        practices_file = os.path.join('./knowledge_base_data', 'best_practices.json')
        if os.path.exists(practices_file):
            with open(practices_file, 'r') as f:
                practices = json.load(f)
                for practice in practices:
                    if query.lower() in practice.get('description', '').lower() or not query:
                        if category == 'all' or category == 'best_practices':
                            results.append({
                                "id": practice.get('id', ''),
                                "title": practice.get('title', ''),
                                "content": practice.get('description', ''),
                                "category": "best_practices",
                                "keywords": practice.get('keywords', []),
                                "date": practice.get('timestamp', '')
                            })
        
        return jsonify(results), 200
    except Exception as e:
        logging.error(f"Error searching knowledge base: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/knowledge/categories', methods=['GET'])
def get_knowledge_categories():
    # Return the available knowledge base categories
    categories = [
        {"id": "all", "name": "All Items"},
        {"id": "rfp_insights", "name": "RFP Insights"},
        {"id": "proposal_feedback", "name": "Proposal Feedback"},
        {"id": "best_practices", "name": "Best Practices"},
        {"id": "lessons_learned", "name": "Lessons Learned"}
    ]
    return jsonify(categories), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    # Simple mock authentication
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    
    # In a real implementation, this would validate against a user database
    if email and password:
        return jsonify({
            "token": "mock-jwt-token",
            "user": {
                "id": "user-1",
                "name": "Demo User",
                "email": email,
                "role": "admin"
            }
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

# CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
