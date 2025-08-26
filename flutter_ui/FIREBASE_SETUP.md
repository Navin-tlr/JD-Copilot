# Firebase Setup Guide for Y² Flutter App

## Prerequisites
- Firebase CLI installed (`npm install -g firebase-tools`)
- Flutter project with Firebase dependencies

## Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name: `y2-copilot` (or your preferred name)
4. Enable Google Analytics (optional)
5. Click "Create project"

## Step 2: Add Flutter App to Firebase
1. In Firebase Console, click "Add app" (</> icon)
2. Select "Flutter"
3. Enter app nickname: `y2-flutter-app`
4. Enter package name: `com.example.flutter_ui`
5. Click "Register app"

## Step 3: Download Configuration Files
1. Download `google-services.json` for Android
2. Download `GoogleService-Info.plist` for iOS
3. Place them in the appropriate directories:
   - Android: `android/app/google-services.json`
   - iOS: `ios/Runner/GoogleService-Info.plist`

## Step 4: Update Firebase Config
1. Open `lib/firebase_config.dart`
2. Replace placeholder values with your actual Firebase config:
   ```dart
   options: const FirebaseOptions(
     apiKey: "YOUR_ACTUAL_API_KEY",
     authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
     projectId: "YOUR_ACTUAL_PROJECT_ID",
     storageBucket: "YOUR_PROJECT_ID.appspot.com",
     messagingSenderId: "YOUR_ACTUAL_SENDER_ID",
     appId: "YOUR_ACTUAL_APP_ID",
     measurementId: "YOUR_ACTUAL_MEASUREMENT_ID",
   ),
   ```

## Step 5: Enable Authentication
1. In Firebase Console, go to "Authentication"
2. Click "Get started"
3. Enable "Email/Password" sign-in method
4. Click "Save"

## Step 6: Enable Firestore Database
1. In Firebase Console, go to "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode" (for development)
4. Select a location close to your users
5. Click "Done"

## Step 7: Set Up Security Rules
1. In Firestore Database, go to "Rules" tab
2. Update rules to allow authenticated users:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /users/{userId} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
     }
   }
   ```

## Step 8: Enable Storage (Optional)
1. In Firebase Console, go to "Storage"
2. Click "Get started"
3. Choose "Start in test mode"
4. Select a location
5. Update storage rules if needed

## Step 9: Test the Setup
1. Run `flutter clean`
2. Run `flutter pub get`
3. Test the app on a device/emulator
4. Check Firebase Console for any errors

## Troubleshooting
- Ensure all configuration files are in the correct locations
- Check that package names match exactly
- Verify Firebase dependencies are properly installed
- Check Firebase Console for authentication errors
- Ensure device has internet connection

## Next Steps
- Implement actual AI/LLM integration in ChatService
- Add more sophisticated error handling
- Implement offline capabilities
- Add push notifications
- Set up analytics and crash reporting
