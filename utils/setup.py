import os

def verify_and_create_structure():
    required_dirs = [
        'data/fetched-files',
        'data/database',
        'logs',
        'fetchers',
        'utils',
        'importers',
        'static',
        'servers'
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"Creating missing directory: {directory}")
            os.makedirs(directory)
        else:
            print(f"Directory exists: {directory}")

if __name__ == "__main__":
    verify_and_create_structure()
