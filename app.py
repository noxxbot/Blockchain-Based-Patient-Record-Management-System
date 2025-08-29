from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
from hashlib import sha256
import json
import secrets
import os
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Enhanced blockchain storage
blockchain = []
pending_records = []

class PatientRecord:
    def __init__(self, name, uid, age, land, medical_condition=None, doctor_name=None, prescription=None):
        self.timestamp = datetime.now()
        self.name = name
        self.age = int(age)
        self.uid = str(uid)
        self.land = land
        self.medical_condition = medical_condition or "General Checkup"
        self.doctor_name = doctor_name or "Dr. Unknown"
        self.prescription = prescription or "None prescribed"
        self.previous_hash = self.calculate_previous_hash()
        self.nonce = 0
        self.hash = self.calculate_hash()
        self.block_id = len(blockchain) + 1
        self.is_verified = False

    def calculate_hash(self):
        """Calculate SHA-256 hash with proof of work"""
        hash_data = (
            str(self.timestamp) + 
            self.name + 
            str(self.uid) + 
            str(self.age) + 
            self.land + 
            self.medical_condition +
            self.doctor_name +
            self.prescription +
            str(self.previous_hash) +
            str(self.nonce)
        )  # ✅ FIXED: Added missing closing parenthesis
        return sha256(hash_data.encode()).hexdigest()

    def calculate_previous_hash(self):
        if len(blockchain) > 0:  # ✅ FIXED: Removed HTML entities
            return blockchain[-1].hash
        return "0000000000000000000000000000000000000000000000000000000000000000"

    def mine_block(self, difficulty=2):
        """Simple proof of work mining"""
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def verify_integrity(self):
        """Verify block integrity"""
        expected_hash = self.calculate_hash()
        return self.hash == expected_hash

    def to_dict(self):
        return {
            'block_id': self.block_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'name': self.name,
            'uid': self.uid,
            'age': self.age,
            'land': self.land,
            'medical_condition': self.medical_condition,
            'doctor_name': self.doctor_name,
            'prescription': self.prescription,
            'hash': self.hash,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'is_verified': self.is_verified
        }  # ✅ FIXED: Added missing closing brace

def verify_blockchain_integrity():
    """Verify the entire blockchain integrity"""
    for i, block in enumerate(blockchain):
        if i == 0:
            if block.previous_hash != "0000000000000000000000000000000000000000000000000000000000000000":
                return False
        else:
            if block.previous_hash != blockchain[i-1].hash:
                return False
        if not block.verify_integrity():
            return False
    return True

# ========== MAIN ROUTES ==========

@app.route('/')
def index():
    stats = {
        'total_records': len(blockchain),
        'total_patients': len(set(block.uid for block in blockchain)),
        'blockchain_integrity': verify_blockchain_integrity(),
        'last_record': blockchain[-1].timestamp.strftime('%Y-%m-%d %H:%M:%S') if blockchain else 'No records yet'
    }  # ✅ FIXED: Added missing closing brace
    return render_template('index.html', stats=stats)

@app.route('/add_record', methods=['GET', 'POST'])
def add_record():
    if request.method == 'POST':
        try:
            name = request.form['name'].strip()
            age = int(request.form['age'])
            land = request.form['land'].strip()
            uid = request.form['uid'].strip()
            medical_condition = request.form.get('medical_condition', '').strip()
            doctor_name = request.form.get('doctor_name', '').strip()
            prescription = request.form.get('prescription', '').strip()

            # Validation
            if not all([name, age, land, uid]):
                flash('All required fields must be filled!', 'error')
                return redirect(url_for('add_record'))

            if age < 0 or age > 150:  # ✅ FIXED: Removed HTML entities
                flash('Please enter a valid age!', 'error')
                return redirect(url_for('add_record'))

            # Create new patient record
            record = PatientRecord(name, uid, age, land, medical_condition, doctor_name, prescription)
            record.mine_block()  # Mine the block with proof of work
            record.is_verified = True
            
            blockchain.append(record)
            
            flash(f'Record added successfully! Block ID: {record.block_id}, Hash: {record.hash[:16]}...', 'success')
            return redirect(url_for('view_blockchain'))

        except ValueError:
            flash('Please enter valid data!', 'error')
            return redirect(url_for('add_record'))
        except Exception as e:
            flash(f'Error adding record: {str(e)}', 'error')
            return redirect(url_for('add_record'))

    return render_template('add_record.html')

@app.route('/search_records')
def search_records():
    return render_template('search_records.html')

@app.route('/get_records', methods=['GET'])
def get_records():
    uid = request.args.get('uid', '').strip()
    if not uid:
        return jsonify({'error': 'UID is required'}), 400

    records = [block.to_dict() for block in blockchain if block.uid == uid]
    if records:
        return jsonify({'success': True, 'records': records, 'total': len(records)})
    return jsonify({'success': False, 'message': 'No records found for this UID'}), 404

@app.route('/view_blockchain')
def view_blockchain():
    blockchain_data = [block.to_dict() for block in blockchain]
    integrity_status = verify_blockchain_integrity()
    return render_template('blockchain.html', 
                         blockchain=blockchain_data, 
                         total_blocks=len(blockchain),
                         integrity_status=integrity_status)

@app.route('/patient_history/<uid>')  # ✅ FIXED: Added missing <uid> parameter
def patient_history(uid):
    history = [block.to_dict() for block in blockchain if block.uid == uid]
    if not history:
        flash('No records found for this patient ID', 'error')
        return redirect(url_for('search_records'))
    
    return render_template('patient_history.html', 
                         history=history, 
                         patient_uid=uid,
                         total_visits=len(history))

# ========== VERIFICATION MODULE ROUTES ==========

@app.route('/verification')
def verification_dashboard():
    """Main verification dashboard"""
    return render_template('verification.html')

@app.route('/verification_report')
def verification_report():
    """Detailed verification report page"""
    return render_template('verification_report.html')

# ========== API ENDPOINTS ==========

@app.route('/api/verify_step_by_step')
def verify_step_by_step():
    """Step-by-step verification with detailed logs"""
    logs = []
    overall_status = True
    
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting blockchain verification...")
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Total blocks to verify: {len(blockchain)}")
    
    if len(blockchain) == 0:
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Blockchain is empty")
        return jsonify({
            'logs': logs,
            'status': 'empty',
            'total_blocks': 0
        })
    
    # Verify each block step by step
    for i, block in enumerate(blockchain):
        logs.append(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📦 Verifying Block #{block.block_id}")
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Patient: {block.name} (ID: {block.uid})")
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Hash: {block.hash[:32]}...")
        
        # Check hash integrity
        calculated_hash = block.calculate_hash()
        if block.hash == calculated_hash:
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Hash integrity: VALID")
        else:
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Hash integrity: INVALID")
            overall_status = False
        
        # Check chain linkage
        if i == 0:
            expected_prev = "0000000000000000000000000000000000000000000000000000000000000000"
            if block.previous_hash == expected_prev:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Genesis block: VALID")
            else:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Genesis block: INVALID")
                overall_status = False
        else:
            if block.previous_hash == blockchain[i-1].hash:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Chain linkage: VALID")
            else:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Chain linkage: BROKEN")
                overall_status = False
        
        # Check proof of work
        if block.hash.startswith('00'):
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Proof of work: VALID (Nonce: {block.nonce})")
        else:
            logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Proof of work: INSUFFICIENT")
    
    logs.append(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🏁 Verification completed!")
    logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Overall status: {'✅ VERIFIED' if overall_status else '❌ COMPROMISED'}")
    
    return jsonify({
        'logs': logs,
        'status': 'verified' if overall_status else 'compromised',
        'total_blocks': len(blockchain)
    })

@app.route('/api/verify_block_by_hash')
def verify_block_by_hash():
    """Verify a single block by hash value"""
    hash_value = request.args.get('hash', '').strip()
    if not hash_value:
        return jsonify({'error': 'Hash value is required'}), 400
    
    # Find block by hash (full match or partial match)
    target_block = None
    for block in blockchain:
        if block.hash == hash_value or block.hash.startswith(hash_value[:16]):
            target_block = block
            break
    
    if not target_block:
        return jsonify({'error': f'Block with hash "{hash_value}" not found. Please check the hash and try again.'}), 404
    
    verification = {
        'block_id': target_block.block_id,
        'patient_name': target_block.name,
        'verification_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stored_hash': target_block.hash,
        'calculated_hash': target_block.calculate_hash(),
        'hash_valid': target_block.hash == target_block.calculate_hash(),
        'nonce': target_block.nonce,
        'mining_valid': target_block.hash.startswith('00'),
        'data_integrity': {
            'name': target_block.name,
            'uid': target_block.uid,
            'age': target_block.age,
            'location': target_block.land,
            'condition': target_block.medical_condition,
            'doctor': target_block.doctor_name,
            'prescription': target_block.prescription
        }  # ✅ FIXED: Added missing closing brace
    }
    
    return jsonify(verification)

@app.route('/api/verify_integrity')
def verify_integrity_api():
    """Comprehensive blockchain integrity verification"""
    start_time = time.time()
    
    verification_report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_blocks': len(blockchain),
        'overall_integrity': True,
        'verification_time_ms': 0,
        'blocks': [],
        'issues': [],
        'statistics': {
            'valid_blocks': 0,
            'invalid_blocks': 0,
            'chain_breaks': 0,
            'hash_mismatches': 0
        }  # ✅ FIXED: Added missing closing brace
    }
    
    # Verify each block
    for i, block in enumerate(blockchain):
        block_verification = {
            'block_id': block.block_id,
            'patient_name': block.name,
            'patient_id': block.uid,
            'timestamp': block.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'stored_hash': block.hash,
            'calculated_hash': block.calculate_hash(),
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'is_valid': True,
            'issues': []
        }  # ✅ FIXED: Added missing closing brace
        
        # Check hash integrity
        if block.hash != block.calculate_hash():
            block_verification['is_valid'] = False
            block_verification['issues'].append('Hash mismatch - block may be tampered')
            verification_report['statistics']['hash_mismatches'] += 1
            verification_report['issues'].append(f'Block #{block.block_id}: Hash integrity compromised')
        
        # Check chain linkage
        if i == 0:
            expected_previous = "0000000000000000000000000000000000000000000000000000000000000000"
            if block.previous_hash != expected_previous:
                block_verification['is_valid'] = False
                block_verification['issues'].append('Genesis block previous hash invalid')
                verification_report['statistics']['chain_breaks'] += 1
        else:
            expected_previous = blockchain[i-1].hash
            if block.previous_hash != expected_previous:
                block_verification['is_valid'] = False
                block_verification['issues'].append('Chain linkage broken - previous hash mismatch')
                verification_report['statistics']['chain_breaks'] += 1
                verification_report['issues'].append(f'Block #{block.block_id}: Chain linkage broken')
        
        # Update statistics
        if block_verification['is_valid']:
            verification_report['statistics']['valid_blocks'] += 1
        else:
            verification_report['statistics']['invalid_blocks'] += 1
            verification_report['overall_integrity'] = False
        
        verification_report['blocks'].append(block_verification)
    
    # Calculate verification time
    verification_report['verification_time_ms'] = round((time.time() - start_time) * 1000, 2)
    
    return jsonify(verification_report)

@app.route('/api/blockchain_health')
def blockchain_health():
    """Overall blockchain health metrics"""
    if not blockchain:
        return jsonify({
            'status': 'empty',
            'health_score': 0,
            'message': 'Blockchain is empty',
            'total_blocks': 0,
            'valid_blocks': 0,
            'chain_integrity': True,
            'last_verified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    total_blocks = len(blockchain)
    valid_blocks = sum(1 for block in blockchain if block.verify_integrity())
    chain_integrity = verify_blockchain_integrity()
    
    health_score = (valid_blocks / total_blocks) * 100 if chain_integrity else 0
    
    return jsonify({
        'status': 'healthy' if health_score == 100 else 'compromised',
        'health_score': health_score,
        'total_blocks': total_blocks,
        'valid_blocks': valid_blocks,
        'chain_integrity': chain_integrity,
        'last_verified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# ========== LEGACY ROUTES ==========

@app.route('/api/blockchain_stats')
def blockchain_stats():
    return jsonify({
        'total_blocks': len(blockchain),
        'total_patients': len(set(block.uid for block in blockchain)),
        'integrity_status': verify_blockchain_integrity(),
        'latest_hash': blockchain[-1].hash if blockchain else None
    })

@app.route('/verify_blockchain')
def verify_blockchain():
    integrity = verify_blockchain_integrity()
    return jsonify({
        'integrity': integrity,
        'total_blocks': len(blockchain),
        'message': 'Blockchain integrity verified' if integrity else 'Blockchain integrity compromised!'
    })

if __name__ == '__main__':
    print("Starting MedChain Blockchain Application...")
    print("Server will be available at: http://localhost:5000")
    print("Available verification endpoints:")
    print("  - /api/verify_step_by_step")
    print("  - /api/verify_block_by_hash")
    print("  - /api/verify_integrity")
    print("  - /api/blockchain_health")
    app.run(debug=True, host='0.0.0.0', port=5000)
