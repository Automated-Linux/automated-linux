
from app.setup.installer import calculate_size, run_installer


if __name__ == "__main__":
    size = calculate_size()
    run_installer(size['columns'], size['lines'], 'vars.yaml')
