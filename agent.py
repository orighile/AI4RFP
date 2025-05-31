"""
Main script to orchestrate the AI RFP Response Agent.

This script will coordinate the different modules of the agent to process an RFP
and generate a proposal response.
"""

import os
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

# Import module logic classes
from input_processing_ingestion_module.module_logic import InputProcessor
from rfp_deconstruction_analysis_module.module_logic import RFPAnalyzer
from compliance_strategy_module.module_logic import ComplianceStrategyDeveloper
from content_generation_module.module_logic import ContentGenerator # Updated to take kb_module
from visual_element_integration_module.module_logic import VisualElementIntegrator
from costing_pricing_module.module_logic import CostingPricingModule
from review_refinement_module.module_logic import ReviewRefinementModule
from output_generation_module.module_logic import OutputGenerationModule
from knowledge_base_learning_module.module_logic import KnowledgeBaseLearningModule

class AiRfpAgent:
    def __init__(self):
        """Initialize the AI RFP Agent and its modules."""
        logging.info("AI RFP Agent Initializing...")
        
        generated_proposals_dir = "./generated_proposals"
        knowledge_base_data_dir = "./knowledge_base_data"

        try:
            # Knowledge Manager must be initialized before Content Generator
            self.knowledge_manager = KnowledgeBaseLearningModule(knowledge_base_dir=knowledge_base_data_dir)
            
            self.input_processor = InputProcessor()
            self.rfp_analyzer = RFPAnalyzer()
            self.compliance_strategist = ComplianceStrategyDeveloper()
            # Pass the knowledge_manager instance to ContentGenerator
            self.content_generator = ContentGenerator(kb_module=self.knowledge_manager) 
            self.visual_integrator = VisualElementIntegrator()
            self.cost_pricer = CostingPricingModule()
            self.reviewer = ReviewRefinementModule()
            self.output_generator = OutputGenerationModule(output_directory=generated_proposals_dir)
            # self.knowledge_manager is already initialized above
            
            logging.info("AI RFP Agent Initialized with all modules (ContentGenerator now uses KnowledgeManager).")
        except Exception as e:
            logging.error(f"Error during AiRfpAgent initialization: {e}", exc_info=True)
            raise

    def process_rfp(self, rfp_file_path, rfp_id, proposal_title, supplementary_docs=None):
        """Process an RFP and generate a response."""
        logging.info(f"--- Starting RFP Processing for RFP ID: {rfp_id}, Title: {proposal_title} ---")
        logging.info(f"RFP File: {rfp_file_path}")

        processed_text = None
        rfp_analysis_data = {}
        compliance_matrix = []
        strategy_elements = {}
        generated_content = {}
        content_with_visuals = {}
        cost_proposal = {}
        review_feedback = {}
        output_file_paths = None

        try:
            # Step 1: Input Processing & Ingestion
            logging.info("Step 1: Input Processing & Ingestion")
            processed_text = self.input_processor.process_document(file_path=rfp_file_path)
            if not processed_text:
                logging.error(f"Failed to process input document {rfp_file_path}. Aborting.")
                return None
            logging.info(f"Successfully processed document. Text length: {len(processed_text)}")

            # Step 2: RFP Deconstruction & Analysis
            logging.info("Step 2: RFP Deconstruction & Analysis")
            rfp_analysis_data = self.rfp_analyzer.extract_key_information(rfp_text_content=processed_text)
            rfp_analysis_data["rfp_id"] = rfp_id
            rfp_analysis_data["proposal_title"] = proposal_title
            # Add fields needed for enhanced RAG filtering, if not already present from analyzer
            # These would ideally come from a more detailed RFP analysis or user input
            rfp_analysis_data.setdefault("client_industry", "General") # Default if not found
            rfp_analysis_data.setdefault("project_domain", "General Services") # Default if not found
            rfp_analysis_data.setdefault("technical_keywords", []) # Default if not found
            logging.info("RFP analysis complete.")

            # Step 3: Compliance & Strategy
            logging.info("Step 3: Compliance & Strategy Development")
            compliance_matrix = self.compliance_strategist.generate_compliance_matrix(rfp_analysis_results=rfp_analysis_data)
            strategy_elements = self.compliance_strategist.develop_initial_strategy(rfp_analysis_results=rfp_analysis_data)
            logging.info(f"Compliance matrix generated ({len(compliance_matrix)} items). Strategy elements developed.")

            # Step 4: Content Generation (now uses enhanced RAG)
            logging.info("Step 4: Content Generation with Enhanced RAG")
            generated_content = self.content_generator.generate_proposal_content(rfp_analysis_data, compliance_matrix, strategy_elements)
            logging.info("Proposal content sections generated.")

            # Step 5: Visual Element Integration
            logging.info("Step 5: Visual Element Integration")
            content_with_visuals = self.visual_integrator.identify_and_integrate_visuals(proposal_content=generated_content)
            logging.info("Visual elements integrated/suggested.")

            # Step 6: Costing & Pricing
            logging.info("Step 6: Costing & Pricing")
            tech_summary = {"complexity_score": rfp_analysis_data.get("complexity_score", 1.1)}
            cost_proposal = self.cost_pricer.develop_cost_proposal(rfp_analysis_output=rfp_analysis_data, technical_proposal_summary=tech_summary)
            logging.info("Cost proposal developed.")

            # Step 7: Review & Refinement
            logging.info("Step 7: Review & Refinement")
            current_review_stage = "Gold Team Final Review"
            review_feedback = self.reviewer.perform_review(proposal_content=content_with_visuals, \
                                                          rfp_analysis_output=rfp_analysis_data, \
                                                          compliance_matrix=compliance_matrix, \
                                                          current_review_stage=current_review_stage)
            logging.info(f"{current_review_stage} review complete.")

            # Step 8: Output Generation
            logging.info("Step 8: Output Generation")
            generated_content_for_output = content_with_visuals
            visual_elements_for_output = content_with_visuals.get("visual_recommendations_summary", [])
            output_file_paths = self.output_generator.generate_proposal_document(
                proposal_title=proposal_title, 
                generated_content=generated_content_for_output, 
                visual_elements=visual_elements_for_output, 
                cost_proposal=cost_proposal, 
                review_feedback_summary=review_feedback
            )
            logging.info(f"Final proposal documents generated at: {output_file_paths}")

        except Exception as e:
            logging.error(f"Error during RFP processing pipeline (Steps 1-8) for RFP ID {rfp_id}: {e}", exc_info=True)

        # Step 9: Knowledge Base Update (attempt even if prior steps had issues, if some data exists)
        logging.info("Step 9: Knowledge Base Update with Enhanced Data")
        try:
            outcome_for_kb = "Processed" # This could be updated later based on actual submission outcome
            if rfp_analysis_data: 
                self.knowledge_manager.store_rfp_insight(
                    rfp_id=rfp_id, 
                    insight_type="Initial RFP Analysis Summary", 
                    content=json.dumps(rfp_analysis_data, indent=2, default=str),
                    keywords=rfp_analysis_data.get("agency_priorities", []) + ["analysis"], 
                    outcome=outcome_for_kb,
                    client_industry=rfp_analysis_data.get("client_industry"),
                    project_domain=rfp_analysis_data.get("project_domain")
                )
            if compliance_matrix:
                for i, item in enumerate(compliance_matrix[:3]): # Store first 3 compliance items as insights
                    item_id = item.get("ID", f"Item_{i+1}")
                    self.knowledge_manager.store_rfp_insight(
                        rfp_id=rfp_id, 
                        insight_type=f'Compliance Item: {item_id}', 
                        content=item.get("Requirement Text", "N/A"), 
                        keywords=["compliance", item_id], 
                        outcome=outcome_for_kb,
                        client_industry=rfp_analysis_data.get("client_industry"),
                        project_domain=rfp_analysis_data.get("project_domain"),
                        related_section=f"Compliance Matrix {item_id}"
                    )
            if review_feedback.get("detailed_feedback"):
                for feedback_item in review_feedback.get("detailed_feedback", []):
                    self.knowledge_manager.store_proposal_feedback(
                        rfp_id=rfp_id, 
                        proposal_version="v1.0", 
                        feedback_source=review_feedback.get("review_stage", "Unknown Review Stage"), 
                        feedback_text=feedback_item.get("comment", "N/A"), 
                        sentiment=feedback_item.get("severity", "Neutral"), # Or map severity to sentiment
                        related_section=feedback_item.get("section")
                    )
            if strategy_elements.get("win_themes"):
                 self.knowledge_manager.store_best_practice(
                    title=f"Strategy Highlights for {proposal_title}", 
                    description=json.dumps(strategy_elements.get("win_themes"), default=str), 
                    category="Proposal Strategy", 
                    keywords=["strategy", rfp_id],
                    applicability=f"{rfp_analysis_data.get('client_industry', 'General')} RFPs"
                )
            # Example of storing a lesson learned (could be more dynamic based on actual outcomes/analysis)
            if generated_content.get("executive_summary") and cost_proposal.get("summary"):
                self.knowledge_manager.store_lesson_learned(
                    rfp_id=rfp_id,
                    lesson_title="Post-Generation Sanity Check",
                    description="Ensured all key components (summary, costing) were generated.",
                    impact="Positive - Process Verification",
                    recommendation="Continue automated checks for completeness.",
                    keywords=["process", "validation"],
                    related_section="Overall Process"
                )
            logging.info("Knowledge base update process completed with enhanced data.")
        except Exception as e:
            logging.error(f"Error during Knowledge Base Update for RFP ID {rfp_id}: {e}", exc_info=True)

        logging.info(f"--- RFP Processing Finished for RFP ID: {rfp_id} ---")
        return output_file_paths

if __name__ == "__main__":
    logging.info("Starting AI RFP Agent main script execution example (Phase 3 RAG Test)...")
    
    try:
        agent = AiRfpAgent()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(os.path.join(base_dir, "test_documents"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "generated_proposals"), exist_ok=True)
        # Ensure KB directory exists, KnowledgeBaseLearningModule also does this but good practice here too
        kb_data_path = os.path.join(base_dir, "knowledge_base_data")
        os.makedirs(kb_data_path, exist_ok=True)
        # Pre-populate KB with some data for the test if empty or for specific test scenarios
        # This would typically be done by running the KB module validation or separate scripts
        # For this test, we rely on the KB module creating its files if they don't exist.
        # And the ContentGenerator test populates its own temp KB.
        # For a full agent run, ensure `knowledge_base_data` has relevant test data.
        # Let's add a sample item to the main KB for the agent.py run to pick up.
        temp_kb_for_agent_run = KnowledgeBaseLearningModule(knowledge_base_dir=kb_data_path)
        if not temp_kb_for_agent_run._read_kb(temp_kb_for_agent_run.insights_file): # if empty
            temp_kb_for_agent_run.store_rfp_insight("RFP-GENERAL-000", "Generic Insight", "Always address client pain points directly.", ["pain points", "client focus"], "Won", "General", "Strategy", "Executive Summary")
            temp_kb_for_agent_run.store_best_practice("General Proposal Tip", "Use clear and concise language.", "Writing Style", ["clarity", "writing"], "All proposals")
            logging.info(f"Populated main KB at {kb_data_path} with initial test data for agent.py run.")

        sample_rfp_file = os.path.join(base_dir, "test_documents", "sample_rfp_phase3.txt") # Use a new file for phase 3 test
        if not os.path.exists(sample_rfp_file):
            with open(sample_rfp_file, "w") as f:
                f.write("This is a sample RFP document for Phase 3 testing of the AI RFP Agent with Advanced RAG.\n")
                f.write("Project Title: NextGen Sky Analytics Platform\n")
                f.write("Client Industry: Aerospace & Defense\n") # For RAG filtering
                f.write("Project Domain: Advanced Data Analytics\n") # For RAG filtering
                f.write("Requirement ID: R-001. Requirement Text: The platform must provide real-time analytics of satellite imagery.\n")
                f.write("Requirement ID: R-002. Requirement Text: The system must integrate with existing ground control systems.\n")
                f.write("Submission Deadline: November 15, 2025.\n")
                f.write("Evaluation Criteria: Technical feasibility, innovation in analytics, and integration capability.\n")
                f.write("Agency Priority: We seek cutting-edge analytical solutions with proven integration patterns.\n")
                f.write("Technical Keywords: satellite, real-time, analytics, integration, AI, machine learning\n")
            logging.info(f"Created dummy RFP file for Phase 3: {sample_rfp_file}")

        rfp_id_example = "RFP-PHASE3-RAG-001"
        proposal_title_example = "Phase 3 RAG Test Proposal for Sky Analytics"

        logging.info(f"Attempting to process RFP: {rfp_id_example} with enhanced RAG.")
        generated_proposal_files = agent.process_rfp(sample_rfp_file, rfp_id_example, proposal_title_example)

        if generated_proposal_files:
            logging.info(f"Generated proposal files: {generated_proposal_files}")
            if "markdown_proposal" in generated_proposal_files:
                 logging.info(f"Main proposal document: {os.path.abspath(generated_proposal_files['markdown_proposal'])}")
        else:
            logging.warning("Proposal generation failed or returned no files.")
    
    except Exception as e:
        logging.critical(f"Critical error in agent __main__ execution (Phase 3 RAG Test): {e}", exc_info=True)
    
    logging.info("Agent script example execution (Phase 3 RAG Test) finished.")
