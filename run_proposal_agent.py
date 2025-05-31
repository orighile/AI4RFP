import argparse
import os
import sys
import logging
import uuid

# Ensure the agent module can be found
# This assumes run_proposal_agent.py is in the same directory as agent.py
# or that the ai_rfp_agent directory is in PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(current_dir)) # If agent.py is one level up in a module structure

from agent import AiRfpAgent # Assuming agent.py is in the same directory or accessible via PYTHONPATH
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
def main():
    parser = argparse.ArgumentParser(description='Run the AI RFP Agent to process an RFP and generate a proposal.')
    parser.add_argument('rfp_file_path', type=str, help='Path to the RFP document file.')
    parser.add_argument('proposal_title', type=str, help='Desired title for the proposal.')

    args = parser.parse_args()

    if not os.path.exists(args.rfp_file_path):
        logging.error(f"RFP file not found: {args.rfp_file_path}")
        print(f"Error: RFP file not found at {args.rfp_file_path}")
        return

    # Generate a unique RFP ID for this run
    # rfp_id = f"RFP-RUN-{os.path.basename(args.rfp_file_path).split('.')[0]}-{uuid.uuid4().hex[:8]}"
    # The agent.py script uses a fixed rfp_id for its main execution, let's make it dynamic here.
    # However, the process_rfp method takes rfp_id as an argument.
    rfp_id = f"AGENT-RUN-{uuid.uuid4().hex[:8]}"

    logging.info(f"Initializing AI RFP Agent for direct processing...")
    try:
        agent_instance = AiRfpAgent()
        logging.info(f"Processing RFP: {args.rfp_file_path} with Title: {args.proposal_title} and ID: {rfp_id}")
        
        # Ensure the knowledge base directory and generated_proposals directory exist relative to agent.py
        # agent_script_dir = os.path.dirname(os.path.abspath(agent_instance.input_processor.__module__.__file__))
        # This is a bit fragile, assuming agent.py is where other modules are relative to.
        # Let's assume agent.py sets up its own relative paths correctly for kb and output.
        # The AiRfpAgent constructor already defines these relative to its own location.

        output_file_paths = agent_instance.process_rfp(
            rfp_file_path=args.rfp_file_path,
            rfp_id=rfp_id,
            proposal_title=args.proposal_title
        )

        if output_file_paths:
            logging.info(f"Proposal generation successful. Output files: {output_file_paths}")
            # Print paths in a machine-readable way if needed, or just user-friendly
            print("Generated proposal documents:")
            for key, path in output_file_paths.items():
                print(f"  {key}: {os.path.abspath(path)}")
        else:
            logging.warning("Proposal generation failed or returned no files.")
            print("Proposal generation did not produce any output files.")

    except ImportError as e:
        logging.critical(f"ImportError: Could not import AiRfpAgent or its dependencies. Ensure agent.py and its modules are in the Python path. Details: {e}", exc_info=True)
        print(f"Error: Failed to import required modules. Please check the agent installation. {e}")
    except Exception as e:
        logging.critical(f"An error occurred during proposal generation: {e}", exc_info=True)
        print(f"Error: An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

