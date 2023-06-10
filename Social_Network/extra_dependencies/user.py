from blockchain_alt import UserBlock

block = UserBlock(username="admin", index=0, previous_hash="0", key='esmmb5r8u6zveps5', timestamp="2023-03-19 21:24:18.183179")
block.mine_block(2)
print(block.hash)
print(block.nonce)
print(len(block.key))