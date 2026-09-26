class MockProvider:

    def generate(self, user_input):
        return {
            "understanding": f"The user said: {user_input}",

            "reasoning": (
                "The situation should be broken into smaller problems "
                "and the most urgent issue should be identified first."
            ),

            "recommendation": (
                "First identify the most urgent task and the deadline "
                "associated with it."
            ),

            "next_step": (
                "Ask the user which task has the closest deadline."
            )
        }