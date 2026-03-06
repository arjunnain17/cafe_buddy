import os
import dotenv
from google import genai
from core.reccomend import recommend

def print_welcome():
    print("=" * 50)
    print(" " * 15 + "Welcome to Cafe Buddy!")
    print("=" * 50)
    print("I can help you find the perfect drink today.")
    print("Just describe what you're in the mood for (e.g., 'something sweet and cold', 'a strong black coffee').")
    print("Type 'quit' or 'exit' at any time to leave.\n")

def print_recommendations(results):
    if not results:
        print("\nI couldn't find any recommendations matching your description perfectly, but here are some options:\n")
        # In a real app we might fetch top 3 generic drinks but recommend() always returns something
    else:
        print(f"\nHere are the top {len(results)} drinks I recommend for you based on your mood:\n")
        
    for r in results:
        print(f"#{r['rank']}: {r['name']} - ₹{r['price']}")
        print(f"Match Score: {r['match']}\n")

def main():
    print_welcome()
    
    while True:
        try:
            print("-" * 50)
            user_input = input("What kind of drink are you craving? > ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nThanks for visiting Cafe Buddy! Enjoy your day.")
                break
                
            if not user_input:
                continue
                
            print("\nThinking... let me check our menu...")
            
            # Get recommendations
            results = recommend(user_input, k=3)
            
            # Display them
            print_recommendations(results)
            
        except KeyboardInterrupt:
            print("\n\nThanks for visiting Cafe Buddy! Enjoy your day.")
            break
        except Exception as e:
            print(f"\nOops, something went wrong: {e}")

if __name__ == "__main__":
    main()
