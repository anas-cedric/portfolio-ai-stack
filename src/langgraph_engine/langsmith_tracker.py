"""
LangSmith Integration for LangGraph.

This module provides LangSmith integration for LangGraph components,
enabling prompt versioning, run tracking, and performance analytics.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic, Union, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv
from langsmith import Client
from langsmith.run_trees import RunTree
from langsmith.schemas import Run
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Type variables for generics
T = TypeVar('T')
U = TypeVar('U')

class LangSmithTracker:
    """
    LangSmith integration for tracking LangGraph runs and versioning prompts.
    
    This class provides a wrapper around LangSmith's client to track runs,
    manage prompt versions, and evaluate performance of LangGraph components.
    """
    
    def __init__(
        self,
        project_name: str = "financial-advisory",
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        prompt_version_tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the LangSmith tracker.
        
        Args:
            project_name: The name of the project in LangSmith
            api_key: Optional LangSmith API key (defaults to LANGCHAIN_API_KEY env var)
            api_url: Optional LangSmith API URL (defaults to LANGCHAIN_ENDPOINT env var)
            prompt_version_tags: Optional tags for prompt versioning
        """
        self.api_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        self.api_url = api_url or os.getenv("LANGCHAIN_ENDPOINT")
        self.project_name = project_name
        self.prompt_version_tags = prompt_version_tags or {}
        
        # Initialize LangSmith client
        try:
            self.client = Client(api_key=self.api_key, api_url=self.api_url)
            logger.info(f"LangSmith client initialized for project: {project_name}")
        except Exception as e:
            logger.warning(f"Could not initialize LangSmith client: {str(e)}")
            self.client = None
    
    def is_active(self) -> bool:
        """
        Check if LangSmith tracking is active.
        
        Returns:
            True if LangSmith tracking is active and properly configured
        """
        return self.client is not None and self.api_key is not None
    
    def track_run(
        self,
        name: str,
        inputs: Dict[str, Any],
        run_type: str = "chain",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Run:
        """
        Track a run in LangSmith.
        
        Args:
            name: Name of the run
            inputs: Input data for the run
            run_type: Type of run (default: "chain")
            tags: Optional tags for the run
            metadata: Optional metadata for the run
            
        Returns:
            Run object for tracking
        """
        if not self.is_active():
            return None
            
        try:
            # Add prompt version tags if available
            all_tags = tags or []
            if name in self.prompt_version_tags:
                all_tags.append(f"version:{self.prompt_version_tags[name]}")
            
            # Add common tags
            all_tags.extend(["financial-advisory", "langgraph", name])
            
            # Create a run with all required fields
            run = Run(
                id=str(uuid.uuid4()),
                name=name,
                inputs=inputs,
                run_type=run_type,
                tags=all_tags,
                metadata=metadata or {},
                project_name=self.project_name,
                start_time=datetime.now(timezone.utc),
                trace_id=str(uuid.uuid4())
            )
            
            # Store the run
            self._current_run = run
            
            return run
            
        except Exception as e:
            logger.error(f"Error tracking run: {str(e)}")
            return None
    
    def end_run(self, run: Run) -> bool:
        """
        End a tracked run.
        
        Args:
            run: The run to end
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_active() or not run:
            return False
            
        try:
            # For newer versions of langsmith where Run.end() might be used instead
            if hasattr(run, 'end'):
                run.end()
            else:
                # Just update the end time attribute for older versions
                if hasattr(run, 'end_time'):
                    run.end_time = datetime.now(timezone.utc)
            
            # Clear current run
            self._current_run = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error ending run: {str(e)}")
            return False
    
    def track_prompt(
        self,
        prompt_name: str,
        prompt_template: str,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Track a prompt version in LangSmith.
        
        Args:
            prompt_name: Name of the prompt
            prompt_template: The prompt template
            version: Optional version identifier (defaults to timestamp)
            tags: Optional tags for the prompt
            
        Returns:
            The version identifier
        """
        if not self.is_active():
            return "langsmith_inactive"
        
        # Generate version if not provided
        if not version:
            version = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Store version in instance
        self.prompt_version_tags[prompt_name] = version
        
        # Prepare tags
        all_tags = tags or []
        all_tags.extend(["prompt", prompt_name, f"version:{version}"])
        
        try:
            # Create a dataset with a single example containing the prompt
            dataset_name = f"{prompt_name}_versions"
            
            # Check if dataset exists
            datasets = self.client.list_datasets(project_name=self.project_name)
            dataset_exists = any(d.name == dataset_name for d in datasets)
            
            if not dataset_exists:
                dataset = self.client.create_dataset(
                    dataset_name=dataset_name,
                    description=f"Versions of the {prompt_name} prompt"
                )
            else:
                dataset = next(d for d in datasets if d.name == dataset_name)
            
            # Add the prompt as an example
            self.client.create_example(
                inputs={"prompt_template": prompt_template},
                outputs={"version": version},
                dataset_id=dataset.id
            )
            
            logger.info(f"Tracked prompt version for {prompt_name}: {version}")
            return version
            
        except Exception as e:
            logger.error(f"Error tracking prompt version: {str(e)}")
            return f"error_{version}"
    
    def get_prompt_versions(self, prompt_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            List of prompt versions
        """
        if not self.is_active():
            return []
        
        try:
            # Find the dataset
            dataset_name = f"{prompt_name}_versions"
            datasets = self.client.list_datasets(project_name=self.project_name)
            dataset = next((d for d in datasets if d.name == dataset_name), None)
            
            if not dataset:
                logger.warning(f"No dataset found for prompt: {prompt_name}")
                return []
            
            # Get examples from the dataset
            examples = self.client.list_examples(dataset_id=dataset.id)
            
            # Extract prompt versions
            versions = []
            for example in examples:
                version = {
                    "version": example.outputs.get("version", "unknown"),
                    "template": example.inputs.get("prompt_template", ""),
                    "created_at": example.created_at
                }
                versions.append(version)
            
            # Sort by creation time (newest first)
            versions.sort(key=lambda x: x["created_at"], reverse=True)
            
            return versions
            
        except Exception as e:
            logger.error(f"Error getting prompt versions: {str(e)}")
            return []
    
    def get_latest_prompt_version(self, prompt_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest version of a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Latest version of the prompt, or None if not found
        """
        versions = self.get_prompt_versions(prompt_name)
        return versions[0] if versions else None
    
    def tracked_fn(self, name: str, tags: Optional[List[str]] = None):
        """
        Decorator for tracking a function with LangSmith.
        
        Args:
            name: Name of the function
            tags: Optional tags for the run
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
            def wrapper(*args, **kwargs):
                if not self.is_active():
                    return func(*args, **kwargs)
                
                # Combine args and kwargs for inputs
                inputs = {
                    "args": args,
                    **kwargs
                }
                
                # Create run
                run_tree = self.track_run(
                    name=name,
                    inputs=inputs,
                    run_type="chain",
                    tags=tags
                )
                
                if not run_tree:
                    return func(*args, **kwargs)
                
                # Execute function and track result
                try:
                    with run_tree:
                        result = func(*args, **kwargs)
                        run_tree.outputs = {"result": result}
                        run_tree.end()
                    return result
                except Exception as e:
                    if run_tree:
                        run_tree.error = str(e)
                        run_tree.end()
                    raise
                
            return wrapper
        return decorator


class PromptVersionManager:
    """
    Manage prompt versions using LangSmith.
    
    This class allows for versioning, tracking, and selecting prompts
    for different LangGraph components.
    """
    
    def __init__(
        self,
        tracker: Optional[LangSmithTracker] = None,
        default_version: str = "current"
    ):
        """
        Initialize the prompt version manager.
        
        Args:
            tracker: LangSmith tracker for version management
            default_version: Default version to use if not specified
        """
        self.tracker = tracker or LangSmithTracker()
        self.default_version = default_version
        self.prompts = {}
        self.current_versions = {}
    
    def register_prompt(
        self,
        prompt_name: str,
        prompt_template: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Register a new prompt version.
        
        Args:
            prompt_name: Name of the prompt
            prompt_template: The prompt template
            version: Optional version identifier
            description: Optional description of the prompt
            tags: Optional tags for the prompt
            
        Returns:
            The version identifier
        """
        # Generate version if tracking is active
        if self.tracker.is_active() and not version:
            version = self.tracker.track_prompt(
                prompt_name=prompt_name,
                prompt_template=prompt_template,
                tags=tags
            )
        elif not version:
            version = "current"
        
        # Store in local registry
        if prompt_name not in self.prompts:
            self.prompts[prompt_name] = {}
        
        self.prompts[prompt_name][version] = {
            "template": prompt_template,
            "description": description or f"Version {version} of {prompt_name}",
            "created_at": datetime.now().isoformat()
        }
        
        # Set as current version
        self.current_versions[prompt_name] = version
        
        return version
    
    def get_prompt(
        self, 
        prompt_name: str,
        version: Optional[str] = None,
        fallback_to_latest: bool = True
    ) -> Optional[str]:
        """
        Get a prompt template by name and version.
        
        Args:
            prompt_name: Name of the prompt
            version: Optional version to retrieve (defaults to current)
            fallback_to_latest: Whether to fall back to latest if version not found
            
        Returns:
            The prompt template, or None if not found
        """
        version = version or self.current_versions.get(prompt_name, self.default_version)
        
        # Try local registry first
        if prompt_name in self.prompts and version in self.prompts[prompt_name]:
            return self.prompts[prompt_name][version]["template"]
        
        # Try LangSmith if tracking is active
        if self.tracker.is_active() and fallback_to_latest:
            latest = self.tracker.get_latest_prompt_version(prompt_name)
            if latest:
                # Cache in local registry
                if prompt_name not in self.prompts:
                    self.prompts[prompt_name] = {}
                
                self.prompts[prompt_name][latest["version"]] = {
                    "template": latest["template"],
                    "description": f"Retrieved from LangSmith: {latest['version']}",
                    "created_at": latest["created_at"].isoformat()
                }
                
                return latest["template"]
        
        return None
    
    def list_prompt_versions(self, prompt_name: str) -> List[Dict[str, Any]]:
        """
        List all versions of a prompt.
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            List of prompt versions
        """
        versions = []
        
        # Get versions from local registry
        if prompt_name in self.prompts:
            for version, info in self.prompts[prompt_name].items():
                versions.append({
                    "version": version,
                    "description": info.get("description", ""),
                    "created_at": info.get("created_at"),
                    "source": "local"
                })
        
        # Get versions from LangSmith if tracking is active
        if self.tracker.is_active():
            langsmith_versions = self.tracker.get_prompt_versions(prompt_name)
            for v in langsmith_versions:
                # Only add if not already in local versions
                if not any(lv["version"] == v["version"] for lv in versions):
                    versions.append({
                        "version": v["version"],
                        "created_at": v["created_at"].isoformat() if hasattr(v["created_at"], "isoformat") else v["created_at"],
                        "source": "langsmith"
                    })
        
        # Sort by creation time (newest first)
        versions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return versions
    
    def set_active_version(self, prompt_name: str, version: str) -> bool:
        """
        Set the active version for a prompt.
        
        Args:
            prompt_name: Name of the prompt
            version: Version to set as active
            
        Returns:
            True if successful, False otherwise
        """
        # Verify version exists
        prompt_exists = (
            prompt_name in self.prompts and version in self.prompts[prompt_name]
        ) or (
            self.tracker.is_active() and 
            any(v["version"] == version for v in self.tracker.get_prompt_versions(prompt_name))
        )
        
        if not prompt_exists:
            return False
        
        # Set as current version
        self.current_versions[prompt_name] = version
        return True


# Helper for integrating with LangGraph decision maker
def wrap_langsmith_decision_maker(
    decision_maker_class: Any,
    tracker: Optional[LangSmithTracker] = None
) -> Any:
    """
    Wrap a decision maker class with LangSmith tracking.
    
    Args:
        decision_maker_class: The decision maker class to wrap
        tracker: Optional LangSmith tracker
        
    Returns:
        Wrapped decision maker class
    """
    if not tracker or not tracker.is_active():
        return decision_maker_class
    
    original_init = decision_maker_class.__init__
    original_make_decision = decision_maker_class.make_decision
    
    def init_wrapper(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.langsmith_tracker = tracker
    
    @tracker.tracked_fn(name="decision_maker", tags=["langgraph", "decision"])
    def make_decision_wrapper(self, *args, **kwargs):
        return original_make_decision(self, *args, **kwargs)
    
    decision_maker_class.__init__ = init_wrapper
    decision_maker_class.make_decision = make_decision_wrapper
    
    return decision_maker_class


# Helper for integrating with LangGraph context retriever
def wrap_langsmith_context_retriever(
    context_retriever_class: Any,
    tracker: Optional[LangSmithTracker] = None
) -> Any:
    """
    Wrap a context retriever class with LangSmith tracking.
    
    Args:
        context_retriever_class: The context retriever class to wrap
        tracker: Optional LangSmith tracker
        
    Returns:
        Wrapped context retriever class
    """
    if not tracker or not tracker.is_active():
        return context_retriever_class
    
    original_init = context_retriever_class.__init__
    original_retrieve = context_retriever_class.retrieve
    
    def init_wrapper(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.langsmith_tracker = tracker
    
    @tracker.tracked_fn(name="context_retriever", tags=["langgraph", "retrieval"])
    def retrieve_wrapper(self, *args, **kwargs):
        return original_retrieve(self, *args, **kwargs)
    
    context_retriever_class.__init__ = init_wrapper
    context_retriever_class.retrieve = retrieve_wrapper
    
    return context_retriever_class 