import logging
import json
import threading

'''
All possible responses must go here. The server will return one response per query, and iterate over them in a circular fashion.
You can use the empty response template below when adding a new response to this list.

Since the chunks are randomly selected, there is not a good way to associate the responses to the chunks at this time. That should
not be necessary for basic testing anyway.
'''
responses = [
   {
        "fact_single":"What are some common ways to assign rewards to partial answers?",
        "fact_single_answer":"There are three: prod , which takes the product of rewards across all steps; min , which selects the minimum reward over all steps; and last, which uses the reward from the final step.",
        "reasoning":"What is the best method for rewarding models?",
        "reasoning_answer":"That depends on whether the training data is prepared using MC rollout, human annotation, or model annotation.",
        "summary":"How does QWEN implement model reward?",
        "summary_answer":"Qwen computes the aggregate reward based on the entire partial reward trajectory. I also uses a method that feeds the performance reference model with partial answers, then only considering the final reward token.",
    },
   ]

empty_response = {
    "fact_single":"",
    "fact_single_answer":"",
    "reasoning":"",
    "reasoning_answer":"",
    "summary":"",
    "summary_answer":"",
}

fact_prompt_match = "I need you to generate three questions that must be answered only with information contained in this passage, and nothing else."

class MockFactGenerator:
    """
    MockFact Generator is a tool that mocks generating a specific sequence of facts.
    """
    def __init__(self, logger:logging.Logger):
        self.logger = logger
        self._lock = threading.Lock()
        self._index = 0

    def generatePair(self, prompt:str):
        ''' 
        generatePair returns a JSON string if the prompt was a Q&A generation prompt, otherwise it returns None.
        '''

        if fact_prompt_match not in prompt:
            self.logger.debug("prompt is not for Q&A gen")
            return None
        
        with self._lock:
            response = responses[self._index]
            self._index = (self._index + 1) % len(responses)
            return json.dumps(response)
