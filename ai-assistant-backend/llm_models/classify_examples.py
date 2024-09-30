from cohere import ClassifyExample

examples = [
    # Time-sensitive examples
    ClassifyExample(text="What are the latest developments in AI?", label="time_sensitive"),
    ClassifyExample(text="Breaking news on the economic summit", label="time_sensitive"),
    ClassifyExample(text="Current trends in renewable energy", label="time_sensitive"),
    ClassifyExample(text="This week's top selling books", label="time_sensitive"),
    ClassifyExample(text="Recent breakthroughs in quantum computing", label="time_sensitive"),
    ClassifyExample(text="How has the stock market performed over the past month?", label="time_sensitive"),
    ClassifyExample(text="What are the upcoming movie releases this summer?", label="time_sensitive"),
    ClassifyExample(text="Latest updates on the ongoing climate conference", label="time_sensitive"),
    ClassifyExample(text="Who are the frontrunners in the upcoming election?", label="time_sensitive"),
    ClassifyExample(text="What were the major scientific discoveries of the past year?", label="time_sensitive"),
    ClassifyExample(text="How has the COVID-19 situation changed in the last few weeks?", label="time_sensitive"),
    ClassifyExample(text="What are the current diplomatic tensions between countries X and Y?", label="time_sensitive"),
    ClassifyExample(text="Recent advancements in electric vehicle technology", label="time_sensitive"),
    ClassifyExample(text="This season's fashion trends", label="time_sensitive"),
    ClassifyExample(text="How have housing prices changed in the last quarter?", label="time_sensitive"),

    # Timeless examples
    ClassifyExample(text="What is the capital of France?", label="timeless"),
    ClassifyExample(text="How does photosynthesis work?", label="timeless"),
    ClassifyExample(text="What are the basic principles of economics?", label="timeless"),
    ClassifyExample(text="Explain the theory of relativity", label="timeless"),
    ClassifyExample(text="Who wrote 'To Kill a Mockingbird'?", label="timeless"),
    ClassifyExample(text="What is the chemical composition of water?", label="timeless"),
    ClassifyExample(text="Describe the process of mitosis", label="timeless"),
    ClassifyExample(text="What are the main themes in Shakespeare's 'Hamlet'?", label="timeless"),
    ClassifyExample(text="How does a combustion engine work?", label="timeless"),
    ClassifyExample(text="What is the significance of the Pythagorean theorem?", label="timeless"),
    ClassifyExample(text="Explain the concept of supply and demand", label="timeless"),
    ClassifyExample(text="What are the main features of Renaissance art?", label="timeless"),
    ClassifyExample(text="How do vaccines work to prevent diseases?", label="timeless"),
    ClassifyExample(text="What is the structure of an atom?", label="timeless"),
    ClassifyExample(text="Describe the water cycle on Earth", label="timeless"),

    # More nuanced or ambiguous examples
    ClassifyExample(text="How has our understanding of dinosaurs changed?", label="time_sensitive"),
    ClassifyExample(text="What are the long-term effects of climate change?", label="timeless"),
    ClassifyExample(text="How do modern interpretations of Shakespeare differ from historical ones?", label="time_sensitive"),
    ClassifyExample(text="What are the enduring impacts of the Industrial Revolution?", label="timeless"),
    ClassifyExample(text="How has the role of women in society evolved over the past century?", label="time_sensitive"),
    ClassifyExample(text="What are the fundamental laws of thermodynamics?", label="timeless"),
    ClassifyExample(text="How do current space exploration efforts compare to those of the 1960s?", label="time_sensitive"),
    ClassifyExample(text="What are the classic symptoms of depression?", label="timeless"),
    ClassifyExample(text="How has the internet changed the way we communicate?", label="time_sensitive"),
    ClassifyExample(text="What are the key differences between major world religions?", label="timeless")
    ]