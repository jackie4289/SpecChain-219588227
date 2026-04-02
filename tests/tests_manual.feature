Feature: Manual checks for the Medito experience

Scenario: TM-01A Close a donation prompt and still start the session
  Given someone opens a session that shows a donation prompt
  When they close the prompt
  Then the same session is still available to start without payment or account creation

Scenario: TM-01B Close a donation prompt while browsing
  Given someone is browsing the app
  When they close a donation prompt
  Then they stay in the same browsing flow and playback is still available

Scenario: TM-02A Browse the app without seeing ads
  Given someone spends 15 minutes moving between the home, course, and player screens
  When they continue browsing normally
  Then no display, video, or audio ad appears

Scenario: TM-02B Finish a session without ad interruptions
  Given someone starts a guided meditation session
  When the session plays all the way through
  Then no third-party ad appears before, during, or after playback

Scenario: TM-03A Open the browse area for emotional needs
  Given someone opens the needs-based browse area
  When the page finishes loading
  Then Anxiety, Stress, Panic, Grief, Anger, and Sleep are all visible as separate options

Scenario: TM-03B Open one needs-based category
  Given someone selects the Anxiety category
  When that category page opens
  Then a list of sessions for anxiety support is shown

Scenario: TM-04A Save a session as a favorite
  Given someone is on a session detail page or player screen
  When they mark the session as a favorite
  Then that session is saved to their favorites

Scenario: TM-04B Start a favorite quickly from home
  Given someone already has at least one saved favorite
  When they open the home screen
  Then a favorite session can be started in no more than two taps

Scenario: TM-05A Show the beginner course in order
  Given someone opens the Beginner course
  When they look through the lesson list
  Then the lessons appear in a fixed order

Scenario: TM-05B Return to the next beginner lesson
  Given someone has completed lesson 1 in the Beginner course
  When they reopen the course
  Then lesson 1 is marked complete and lesson 2 is shown as the next lesson

Scenario: TM-06A Set a daily reminder
  Given someone opens the reminder settings
  When they enable a reminder for 21:00 local time
  Then that time is saved and one daily notification is scheduled

Scenario: TM-06B Turn a daily reminder off
  Given someone already has an active reminder
  When they disable it
  Then no active daily reminder remains scheduled

Scenario: TM-07A Open the Sleep section
  Given someone opens the Sleep section
  When it loads
  Then sleep meditations, sleep stories, and sleep sounds appear as separate sections

Scenario: TM-07B Open each sleep subsection
  Given someone is already in the Sleep section
  When they open each subsection
  Then each one shows its own sleep-related list of content

Scenario: TM-08A Let one sleep track roll into the next
  Given someone creates a queue with two sleep tracks
  When the first track finishes
  Then the second track starts automatically without a blocking popup

Scenario: TM-08B Repeat a sleep track without interruption
  Given someone turns on repeat for a sleep track
  When the track reaches the end
  Then it restarts automatically without a blocking popup

Scenario: TM-09A Keep playback going with the screen off
  Given someone starts a session with headphones connected
  When the screen stays off for 10 minutes
  Then the audio keeps playing and the app does not crash

Scenario: TM-09B Come back to the app after screen-off playback
  Given someone starts a session and turns the screen off
  When they reopen the app after 10 minutes
  Then the session is still active and the playback controls still respond

Scenario: TM-10A See progress carry over to another device
  Given the same account is signed in on device A and device B
  When someone completes one course lesson on device A
  Then device B shows the completed lesson and updated streak count within 60 seconds of sync

Scenario: TM-10B Get progress back after signing in again
  Given someone signs back in with an account that already has progress
  When sync finishes
  Then the earlier streak count and completed lessons are restored within 60 seconds
