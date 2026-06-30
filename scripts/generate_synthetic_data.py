import datetime
import random
import json
import os

# Define Taxonomies (Matching Flutter Models)
MOODS = ['Terrible', 'Bad', 'Neutral', 'Good', 'Excellent']

EMOTIONS = [
    'Numb', 'Adoring', 'Angry', 'Confused', 'Sad', 'Fearful', 
    'Embarrassed', 'Mischievous', 'Amused', 'Loved', 'Shocked', 
    'Happy', 'Exhausted', 'Excited', 'Frustrated', 'Anxious', 
    'Disgusted', 'Content', 'Playful', 'Lost'
]

REASONS = [
    'Work', 'School & Studies', 'Deadlines', 'Productivity', 'Coworkers', 
    'Family', 'Friends', 'Relationship', 'Socializing', 'Conflict', 
    'Loneliness', 'Sleep', 'Exercise', 'Hobby & Play', 'Food & Diet', 
    'Chores & Errands', 'Commute', 'Physical Health', 'Mental Well-being', 
    'Stress', 'Anxiety', 'Relaxation', 'Self-Care', 'Travel & Outing', 
    'Weather', 'Pets', 'Entertainment', 'Finances', 'Personal Growth', 
    'Success & Milestone', 'Setbacks', 'Future Plans'
]

# Note Templates by context to ensure high semantic value for RAG queries
UNI_TEMPLATES = {
    'stressed': [
        "So overwhelmed with exam prep. Feel like my head is going to explode.",
        "Spent 6 hours in the library. Still don't understand this calculus chapter.",
        "Another group project where I'm doing all the work. So frustrating.",
        "Midterm grades came back. I passed but expected much higher. Disappointed.",
        "Up late studying. Eyes are burning and I can't concentrate anymore."
    ],
    'normal': [
        "Lectures were pretty boring today. Just took notes and listened to music.",
        "Grabbed coffee between classes with a classmate. Nice break.",
        "Got some study goals checked off today. Feel decent.",
        "Class got cancelled today, so I got to go home early. Happy about that.",
        "Usual college routine today. Just trying to stay on top of the readings."
    ]
}

JOB_HUNT_TEMPLATES = {
    'rejection': [
        "Received another standard rejection email. 'Unfortunately, we chose to proceed with other candidates...' Feeling useless.",
        "Ghosted by the company I interviewed with last week. It's so discouraging.",
        "Spent the entire morning modifying my CV for the hundredth time. I'm so tired of this.",
        "Applied to 10 more jobs today. Feels like shouting into a void.",
        "Felt so qualified for that role. Why didn't they even call me for an interview?"
    ],
    'family_pressure': [
        "Parents asked about job applications again at dinner. I know they care, but it feels like constant pressure.",
        "Had an argument with my dad about my career path. He doesn't understand how tough the market is right now.",
        "Mom hinted that I should take any minimum wage job. I feel like a disappointment.",
        "Tension is high at home. Wish I had my own place, but I can't afford it without a job.",
        "Frustrated. Everyone acts like I'm not trying, but I'm applying to roles daily."
    ],
    'success': [
        "Oh my god! I got a call back for a second-round interview! Hopeful!",
        "The recruiter said my portfolio looked amazing. What a relief.",
        "I landed the job! I got the offer letter today! I cannot believe it. Start date is next month!",
        "Signed my contract! The pay is decent, and the team seems friendly. A massive weight off my shoulders.",
        "Told my parents I finally got hired. The relief in the house is palpable."
    ]
}

CAREER_TEMPLATES = {
    'stressed': [
        "Work was chaotic today. Back-to-back meetings and a massive backlog.",
        "Dealing with a bug in production. Deadline pressure is hitting hard.",
        "Coworkers are dumping their tasks on me. Frustrated with the team dynamic.",
        "Got some critical feedback from my manager. Triggered my imposter syndrome big time.",
        "Worked late to finish the presentation. Exhausted and ready to log off."
    ],
    'normal': [
        "A productive day at the office. Got through my backlog.",
        "Had a nice lunch chat with some coworkers. Feeling more settled here.",
        "Met my milestones for the week. Feels good to be on track.",
        "Typical day of coding and emails. Stable and quiet.",
        "Manager praised my work in the standup. Small boost in confidence."
    ]
}

WINTER_DEPRESSION_TEMPLATES = [
    "It's 4 PM and already pitch black outside. This winter weather drains all my energy.",
    "Woke up feeling empty and numb. Didn't want to get out of bed today.",
    "Felt incredibly lonely today. Just stared at my phone waiting for a message.",
    "No energy to cook or clean. Ended up ordering takeout and sleeping early.",
    "Feeling lost and disconnected from everyone. Winters are always the hardest.",
    "It's freezing and gray. Seasonal blues are hitting hard this week.",
    "Just felt this heavy sadness all afternoon for no specific reason."
]

WEEKEND_POS_TEMPLATES = [
    "Had an amazing date night. We tried a new Italian place and walked around the park.",
    "Met up with my college friends for dinner. Laughed so much, I needed this.",
    "Spent the morning painting and listening to records. Perfect self-care day.",
    "Went on a weekend hike. Getting out into nature really helped clear my anxiety.",
    "Movie night and pizza. Feeling incredibly loved and safe today.",
    "Spent the afternoon playing video games and relaxing. Great weekend recovery."
]

def generate_entry(dt, phase, is_winter, is_weekend, time_slot):
    # Determine mood probabilities based on phase and modifiers
    mood_weights = [0.1, 0.2, 0.4, 0.2, 0.1] # Default weights: Terrible, Bad, Neutral, Good, Excellent
    
    # Apply modifiers
    if is_winter:
        mood_weights[0] += 0.15 # Increase Terrible
        mood_weights[1] += 0.25 # Increase Bad
        mood_weights[3] -= 0.15 # Decrease Good
        mood_weights[4] -= 0.15 # Decrease Excellent
    
    if phase == 'job_hunt' and not is_weekend:
        mood_weights[0] += 0.15
        mood_weights[1] += 0.20
        mood_weights[3] -= 0.15
        
    if is_weekend:
        mood_weights[0] -= 0.05
        mood_weights[1] -= 0.10
        mood_weights[3] += 0.20
        mood_weights[4] += 0.15

    # Normalize weights
    mood_weights = [max(0.01, w) for w in mood_weights]
    total_w = sum(mood_weights)
    mood_weights = [w / total_w for w in mood_weights]

    mood = random.choices(MOODS, weights=mood_weights, k=1)[0]

    # Map mood to emotions and reasons
    emotions = []
    reasons = []
    notes = ""

    # Choose template and tags based on mood and phase
    if mood in ['Terrible', 'Bad']:
        # Choose negative emotions
        emotions = random.sample(['Sad', 'Anxious', 'Frustrated', 'Exhausted', 'Lost', 'Numb', 'Fearful'], k=random.randint(1, 3))
        
        # Determine notes based on context
        if is_winter and random.random() < 0.6:
            notes = random.choice(WINTER_DEPRESSION_TEMPLATES)
            reasons.extend(['Weather', 'Mental Well-being', 'Loneliness'])
        elif phase == 'university':
            if time_slot in ['afternoon', 'night']:
                notes = random.choice(UNI_TEMPLATES['stressed'])
                reasons.extend(['School & Studies', 'Deadlines', 'Stress'])
            else:
                notes = "Felt anxious starting the day. Too much studying to do."
                reasons.extend(['School & Studies', 'Anxiety'])
        elif phase == 'job_hunt':
            if random.random() < 0.6:
                notes = random.choice(JOB_HUNT_TEMPLATES['rejection'])
                reasons.extend(['Setbacks', 'Finances', 'Future Plans'])
            else:
                notes = random.choice(JOB_HUNT_TEMPLATES['family_pressure'])
                reasons.extend(['Family', 'Conflict', 'Stress'])
        elif phase == 'career':
            notes = random.choice(CAREER_TEMPLATES['stressed'])
            reasons.extend(['Work', 'Deadlines', 'Stress'])
        else:
            notes = "Just a rough day overall. Feeling low energy."
            reasons.append('Mental Well-being')

    elif mood == 'Neutral':
        emotions = random.sample(['Content', 'Confused', 'Exhausted', 'Numb', 'Playful'], k=random.randint(1, 2))
        reasons.append('Sleep' if time_slot == 'morning' else 'Chores & Errands')
        
        if phase == 'university':
            notes = random.choice(UNI_TEMPLATES['normal'])
            reasons.append('School & Studies')
        elif phase == 'career':
            notes = random.choice(CAREER_TEMPLATES['normal'])
            reasons.append('Work')
        else:
            notes = "Just going through the motions today. Nothing special happened."
            reasons.append('Routine' if 'Routine' in REASONS else 'Productivity')

    else: # Good, Excellent
        emotions = random.sample(['Happy', 'Loved', 'Excited', 'Content', 'Amused', 'Playful', 'Adoring'], k=random.randint(1, 3))
        
        if is_weekend:
            notes = random.choice(WEEKEND_POS_TEMPLATES)
            reasons.extend(['Socializing', 'Friends', 'Relaxation'])
            if 'Loved' in emotions or 'Adoring' in emotions:
                reasons.append('Relationship')
        elif phase == 'job_hunt' and random.random() < 0.15: # Trigger a job application success
            notes = random.choice(JOB_HUNT_TEMPLATES['success'])
            reasons.extend(['Success & Milestone', 'Future Plans', 'Personal Growth'])
        elif phase == 'career':
            notes = "Had a great productive day at work. Smashed my tasks."
            reasons.extend(['Work', 'Productivity', 'Personal Growth'])
        else:
            notes = "Had a good workout today and cooked a healthy dinner. Feeling great."
            reasons.extend(['Exercise', 'Food & Diet', 'Self-Care'])

    # Add general time slot variations
    if time_slot == 'morning':
        reasons.append('Sleep')
        if mood in ['Terrible', 'Bad']:
            notes += " Woke up with a headache."
    elif time_slot == 'night':
        reasons.append('Relaxation' if mood in ['Good', 'Excellent'] else 'Sleep')

    # Remove duplicates and ensure tags match standard list
    reasons = list(set([r for r in reasons if r in REASONS]))
    emotions = list(set([e for e in emotions if e in EMOTIONS]))
    
    # Truncate notes if empty (fallback)
    if not notes:
        notes = "Felt okay today. Just normal things."

    return {
        "timestamp": dt.isoformat(),
        "mood": mood,
        "emotions": emotions,
        "reasons": reasons,
        "notes": notes,
        "userId": "aria_simulated_user_id"
    }

def main():
    print("Starting synthetic data generation...")
    
    # 3 Years Timeline
    start_date = datetime.date(2023, 6, 30)
    end_date = datetime.date(2026, 6, 30)
    
    entries = []
    current_date = start_date
    delta = datetime.timedelta(days=1)
    
    total_days = (end_date - start_date).days + 1
    print(f"Generating data for {total_days} days...")

    # Time slots configuration
    time_slots = {
        'early_morning': (6, 7),
        'morning': (8, 10),
        'midday': (12, 13),
        'afternoon': (15, 16),
        'evening': (18, 20),
        'night': (22, 23)
    }

    while current_date <= end_date:
        # Determine Phase
        # Year 1: Uni (Up to May 31, 2024)
        if current_date <= datetime.date(2024, 5, 31):
            phase = 'university'
        # Year 2: Job hunt (June 1, 2024 to Feb 28, 2025)
        elif current_date <= datetime.date(2025, 2, 28):
            phase = 'job_hunt'
        # Year 3: Career (March 1, 2025 onwards)
        else:
            phase = 'career'

        # Special life milestone triggers (independent of random weight changes)
        is_graduation_day = (current_date == datetime.date(2024, 6, 15))
        is_job_offer_day = (current_date == datetime.date(2025, 3, 5))
        is_first_day_of_work = (current_date == datetime.date(2025, 3, 17))

        is_winter = current_date.month in [11, 12, 1, 2] # November to February
        is_weekend = current_date.weekday() in [5, 6] # Saturday, Sunday

        # Generate 5-6 entries for this day
        num_entries = random.choices([5, 6], weights=[0.5, 0.5])[0]
        slots_to_generate = random.sample(list(time_slots.keys()), k=num_entries)
        
        # Sort slots by chronological order
        ordered_slots = ['early_morning', 'morning', 'midday', 'afternoon', 'evening', 'night']
        slots_to_generate.sort(key=lambda x: ordered_slots.index(x))

        for slot in slots_to_generate:
            hr_range = time_slots[slot]
            hour = random.randint(hr_range[0], hr_range[1])
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            dt = datetime.datetime(
                current_date.year, current_date.month, current_date.day,
                hour, minute, second
            )

            # Check special milestone overrides
            if is_graduation_day:
                entry = {
                    "timestamp": dt.isoformat(),
                    "mood": "Excellent",
                    "emotions": ["Happy", "Excited", "Loved"],
                    "reasons": ["Success & Milestone", "Friends", "Family", "Personal Growth"],
                    "notes": "Graduated today! Can't believe these 4 years are over. Celebrated with family and friends. So happy and excited for the future!",
                    "userId": "aria_simulated_user_id"
                }
            elif is_job_offer_day and slot == 'midday':
                entry = {
                    "timestamp": dt.isoformat(),
                    "mood": "Excellent",
                    "emotions": ["Happy", "Excited", "Content"],
                    "reasons": ["Success & Milestone", "Finances", "Future Plans"],
                    "notes": "I GOT THE JOB OFFER! The HR manager called me during lunch. I'm starting as a Junior Developer next week! Crying happy tears right now.",
                    "userId": "aria_simulated_user_id"
                }
            elif is_first_day_of_work and slot == 'morning':
                entry = {
                    "timestamp": dt.isoformat(),
                    "mood": "Good",
                    "emotions": ["Anxious", "Excited"],
                    "reasons": ["Work", "Stress", "Future Plans"],
                    "notes": "First day of work! On the commute now. Feeling a mix of extreme excitement and imposter anxiety. Let's do this.",
                    "userId": "aria_simulated_user_id"
                }
            else:
                entry = generate_entry(dt, phase, is_winter, is_weekend, slot)
                
            entries.append(entry)

        current_date += delta

    # Create scripts folder if not exists
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Save to JSON
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_mood_data.json")
    with open(json_path, "w") as f:
        json.dump(entries, f, indent=2)

    # Print summary statistics
    print(f"\nSuccessfully generated {len(entries)} mood entries!")
    print(f"Data saved to {json_path}")
    
    # Simple statistics verification
    mood_counts = {m: 0 for m in MOODS}
    for entry in entries:
        mood_counts[entry['mood']] += 1
        
    print("\nMood Distribution:")
    for mood, count in mood_counts.items():
        percentage = (count / len(entries)) * 100
        print(f" - {mood}: {count} ({percentage:.2f}%)")

if __name__ == "__main__":
    main()
