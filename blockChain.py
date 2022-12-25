import hashlib
from time import time
import json
from uuid import uuid4
from  urlparse import urlparse
import requests

class Blockchain(object):

    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes=set()
        
        
        #Creates the genesis block
        print("Initialize the genesis block")
        self.new_block(previous_hash=1, proof=100)
        print(self.chain)

    def register_node(self,address):
        """
        Add a node to the list of Nodes
        :param address:<str> IP Address of the Node Eg:'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self,proof,previous_hash=None):

        """
        Creates the new block in the blockchain
        :param proof:<str> The proof provided by the miner
        :param previous_hash:Optional <str> The Hash of the previous block
        :return: <dict> Newly created block
        """

        block = {
            'index':len(self.chain) + 1,
            'timestamp':time(),
            'transactions':self.current_transactions, 
            'proof':proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
                }
        
        #resetting the current transactions
        self.current_transactions = []

        #Adding the block to the chain
        self.chain.append(block)

        return block 

    def new_transactions(self,sender,recipient,amount):
        """
        Create new transactions and adds it to the transaction pool

        :param sender: <str> Address of the sender
        :param recipient: <str> Address of the Receiver 
        :param amount: <int> Amount
        :return: <int> The index of the Block that would hold this transaction
        """
        self.current_transactions.append(
            {
                'sender':sender,
                'recipient':recipient,
                'amount': amount
            }
            )
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates SHA-256 hash of the block

        param:block: <dict> Block
        return:<str>
        """
        #Order of the Key Value pairs should be ordered to avoid different hash values
        block_string = json.dumps(block,sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()


    def proof_of_work(self,last_proof):
        """
        Basic proof of work 
        - Find a number p' such that hash(pp') meets the 4 leading zero constraint
        :param:last_proof:<int>
        :return:<int>

        """

        proof = 0
        print('PoW Started')
        while self.valid_proof(last_proof,proof) is False:
            proof += 1
        print('PoW Ended')
        return proof 
    
    @staticmethod
    def valid_proof(last_proof,proof):
        """
        Validates the proof - checks whether hash(last_proof,proof) meets the leading zeroes constraint

        :param:last_proof:<int>
        :param:proof:<int>
        :return:<bool> True if correct, False if it doesn't match
        """
        guess = '{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def valid_chain(self,chain):
        """
        Determine if a given blockchain is valid

        :param chain:<list> A blockchain
        :return:<bool> True if valid
        """

        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block=chain[current_index]
            print("{last_block}")
            print("{block}")
            print("\n-----------\n")
            #checking the hash of the block is correct 
            if block['previous_hash'] != self.hash(last_block):
                return False
            
            #Checking the PoW is correct 
            if not self.proof_of_work(last_block['proof']):
                return False

            last_block  = block 
            current_index +=1
        
        return True
    
    def resolve_conflicts(self):
        """
        This is the consensus algorithm which helps in resolving the chain inconsistency 

        :return:<bool> True if our chain was replaced
        """

        neighbours = self.nodes
        new_chain = None

        #Idenitfying the longest chain within the nodes
        max_length = len(self.chain)

        #Get the chain from all the registered node and validate
        for node in neighbours:
            response = requests.get("http://{node}/chain")

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

            #Checking if the retrieved chain is lengthier and valid    
            if length > max_length and self.valid_chain(chain):
                max_length = length 
                new_chain = chain 
        
        #checking if we lengthier chain from neightbours
        if new_chain:
            self.chain = new_chain
            return True
        
        return False

