# Hybrid Specification

## Requirement ID: FR_hybrid_1
- Description: [Donation prompts should stay optional, and closing one should never block access to the selected session.]
- Source Persona: [P_hybrid_1 - Budget-Conscious Free User]
- Traceability: [Derived from hybrid review group A1]
- Acceptance Criteria: [Given someone closes a donation prompt while browsing or before playback, when the prompt disappears, then the selected session remains available to start without payment or account creation.]

## Requirement ID: FR_hybrid_2
- Description: [Core meditation and sleep content should remain free of third-party ads and subscription gates during browsing and playback.]
- Source Persona: [P_hybrid_1 - Budget-Conscious Free User]
- Traceability: [Derived from hybrid review group A1]
- Acceptance Criteria: [Given someone spends 15 minutes browsing the home, library, and player screens and completes one session, when that flow ends, then no third-party ad appears and no subscription is required to continue into playback.]

## Requirement ID: FR_hybrid_3
- Description: [The Sleep area should list sleep meditations, sleep stories, and sleep sounds as separate sections.]
- Source Persona: [P_hybrid_2 - Bedtime Listener]
- Traceability: [Derived from hybrid review group A2]
- Acceptance Criteria: [Given someone opens the Sleep area, when it loads, then sleep meditations, sleep stories, and sleep sounds appear as three separate sections.]

## Requirement ID: FR_hybrid_4
- Description: [Sleep playback should support repeat and track queues without showing a blocking popup between tracks.]
- Source Persona: [P_hybrid_2 - Bedtime Listener]
- Traceability: [Derived from hybrid review group A2]
- Acceptance Criteria: [Given someone queues two sleep tracks or turns on repeat for one sleep track, when the first playback ends, then the next track starts or the same track restarts automatically and no blocking popup interrupts playback.]

## Requirement ID: FR_hybrid_5
- Description: [The app should group support sessions under named categories including Anxiety, Stress, Panic, Grief, and Anger.]
- Source Persona: [P_hybrid_3 - Emotional Support Seeker]
- Traceability: [Derived from hybrid review group A3]
- Acceptance Criteria: [Given someone opens the support or needs-based browse area, when it loads, then Anxiety, Stress, Panic, Grief, and Anger appear as separate categories and each one opens its own session list.]

## Requirement ID: FR_hybrid_6
- Description: [The app should let someone save a session as a favorite and start it again from the home screen in no more than two taps.]
- Source Persona: [P_hybrid_3 - Emotional Support Seeker]
- Traceability: [Derived from hybrid review group A3]
- Acceptance Criteria: [Given someone has already saved at least one favorite, when they open the home screen, then a saved favorite is visible there and can be started in two taps or fewer.]

## Requirement ID: FR_hybrid_7
- Description: [The Beginner course should keep lessons in order and show the next unfinished lesson when someone returns.]
- Source Persona: [P_hybrid_4 - Habit-Building Beginner]
- Traceability: [Derived from hybrid review group A4]
- Acceptance Criteria: [Given someone completes lesson 1 in the Beginner course, when they reopen that course, then lesson 1 is marked complete and lesson 2 is shown as the next lesson.]

## Requirement ID: FR_hybrid_8
- Description: [The app should let someone schedule one daily reminder at a chosen local time and turn it off later.]
- Source Persona: [P_hybrid_4 - Habit-Building Beginner]
- Traceability: [Derived from hybrid review group A4]
- Acceptance Criteria: [Given someone enables a daily reminder for 21:00 local time, when the reminder is saved, then one daily notification is scheduled for 21:00 and remains scheduled until the reminder is turned off.]

## Requirement ID: FR_hybrid_9
- Description: [A session should keep playing for at least 10 minutes with the screen off and wired or Bluetooth headphones connected, without crashing or stopping before the 10-minute mark.]
- Source Persona: [P_hybrid_5 - Reliability-Focused Regular User]
- Traceability: [Derived from hybrid review group A5]
- Acceptance Criteria: [Given someone starts a session, turns the screen off, and keeps wired or Bluetooth headphones connected, when 10 minutes pass, then audio is still playing, the app has not crashed, and playback controls respond after reopening the app.]

## Requirement ID: FR_hybrid_10
- Description: [A signed-in user's streak and completed course lessons should be restored after sign-in and should sync to another device within 60 seconds.]
- Source Persona: [P_hybrid_5 - Reliability-Focused Regular User]
- Traceability: [Derived from hybrid review group A5]
- Acceptance Criteria: [Given a signed-in user completes a course lesson on device A, when the same account is opened on device B or signs in again on the original device, then the updated streak count and completed lesson appear within 60 seconds after sync finishes.]
