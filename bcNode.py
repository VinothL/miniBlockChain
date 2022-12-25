from blockChain import Blockchain
from flask import Flask,jsonify,request
import json
from uuid import uuid4 
from textwrap import dedent

#Instantiate the Node 
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')


#Instantiate the Blockchain
print('Loading the blockchain class')
blockchain = Blockchain()


@app.route('/mine',methods=['GET'])
def mine():
    #We run the proof of work to generate the proof
    print(blockchain.chain)
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    #Block miners are credited with new coins 
    blockchain.new_transactions(
        sender = "0",
        recipient = node_identifier,
        amount = 1,
    )

    #Forge the new block to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof,previous_hash)

    response = {
        'message': "New block has been forged",
        'index':block['index'],
        'transactions':block['transactions'],
        'proof':block['proof'],
        'previous_hash':block['previous_hash'],
    }

    return jsonify(response), 200




@app.route('/transactions/new',methods=['POST'])
def new_transactions():
    values = request.get_json()

    #check if the required fields are there in the POSTed
    required=['sender','recipient','amount']
    if not all(k in values for k in required):
        return 'Missing Values',400

    #Creates a new transaction
    index = blockchain.new_transactions(values['sender'],values['recipient'],values['amount'])
    message = "New Transaction will be added to the block {}".format(index)
    response = {'message':message }
    return jsonify(response),201


@app.route('/chain',methods=['GET'])
def full_chain():
    response = {
        'chain':blockchain.chain,
        'length':len(blockchain.chain),
    }

    return jsonify(response),200


@app.route('/nodes/register',methods = ['POST'])
def register_node():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply list of valid nodes",400
    
    for node in nodes:
        blockchain.register_node(node)
    
    response = {
        'message' :'New Nodes has been added to the list',
        'total_nodes' :list(blockchain.nodes),
    }

    return jsonify(response),201


@app.route('/nodes/resolve',methods =['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message' :'Our chain was replaced',
            'new_chain' : blockchain.chain,
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1',port=5000)
    