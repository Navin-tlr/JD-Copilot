// Replace this file with your actual Firebase configuration
// This is a template - you need to fill in your real Firebase project details

import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Your actual Firebase configuration
/// Replace the placeholder values with your real Firebase project details
class RealFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        return windows;
      case TargetPlatform.linux:
        throw UnsupportedError(
          'Firebase is not configured for linux platform.',
        );
      default:
        throw UnsupportedError(
          'Firebase is not configured for this platform.',
        );
    }
  }

  // TODO: Replace these with your actual Firebase Web configuration
  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'YOUR_ACTUAL_WEB_API_KEY', // Replace this
    appId: 'YOUR_ACTUAL_WEB_APP_ID', // Replace this
    messagingSenderId: 'YOUR_ACTUAL_SENDER_ID', // Replace this
    projectId: 'YOUR_ACTUAL_PROJECT_ID', // Replace this
    authDomain: 'YOUR_ACTUAL_PROJECT_ID.firebaseapp.com', // Replace this
    storageBucket: 'YOUR_ACTUAL_PROJECT_ID.appspot.com', // Replace this
    measurementId: 'YOUR_ACTUAL_MEASUREMENT_ID', // Replace this (optional)
  );

  // TODO: Replace these with your actual Firebase Android configuration
  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'YOUR_ACTUAL_ANDROID_API_KEY', // Replace this
    appId: 'YOUR_ACTUAL_ANDROID_APP_ID', // Replace this
    messagingSenderId: 'YOUR_ACTUAL_SENDER_ID', // Replace this
    projectId: 'YOUR_ACTUAL_PROJECT_ID', // Replace this
    storageBucket: 'YOUR_ACTUAL_PROJECT_ID.appspot.com', // Replace this
  );

  // TODO: Replace these with your actual Firebase iOS configuration
  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'YOUR_ACTUAL_IOS_API_KEY', // Replace this
    appId: 'YOUR_ACTUAL_IOS_APP_ID', // Replace this
    messagingSenderId: 'YOUR_ACTUAL_SENDER_ID', // Replace this
    projectId: 'YOUR_ACTUAL_PROJECT_ID', // Replace this
    storageBucket: 'YOUR_ACTUAL_PROJECT_ID.appspot.com', // Replace this
    iosBundleId: 'com.example.flutterUi', // This should match your iOS bundle ID
  );

  // TODO: Replace these with your actual Firebase macOS configuration
  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: 'YOUR_ACTUAL_MACOS_API_KEY', // Replace this
    appId: 'YOUR_ACTUAL_MACOS_APP_ID', // Replace this
    messagingSenderId: 'YOUR_ACTUAL_SENDER_ID', // Replace this
    projectId: 'YOUR_ACTUAL_PROJECT_ID', // Replace this
    storageBucket: 'YOUR_ACTUAL_PROJECT_ID.appspot.com', // Replace this
    iosBundleId: 'com.example.flutterUi', // This should match your macOS bundle ID
  );

  // TODO: Replace these with your actual Firebase Windows configuration
  static const FirebaseOptions windows = FirebaseOptions(
    apiKey: 'YOUR_ACTUAL_WINDOWS_API_KEY', // Replace this
    appId: 'YOUR_ACTUAL_WINDOWS_APP_ID', // Replace this
    messagingSenderId: 'YOUR_ACTUAL_SENDER_ID', // Replace this
    projectId: 'YOUR_ACTUAL_PROJECT_ID', // Replace this
    storageBucket: 'YOUR_ACTUAL_PROJECT_ID.appspot.com', // Replace this
  );
}

/*
INSTRUCTIONS TO COMPLETE SETUP:

1. Go to Firebase Console: https://console.firebase.google.com
2. Select your project
3. Go to Project Settings (gear icon)
4. Add Flutter app if not already done
5. Copy the configuration values from your Firebase project
6. Replace all "YOUR_ACTUAL_*" values in this file
7. Save the file
8. Update firebase_config.dart to use RealFirebaseOptions instead of DefaultFirebaseOptions

Example of what your web config might look like:
static const FirebaseOptions web = FirebaseOptions(
  apiKey: 'AIzaSyC1234567890abcdefghijklmnopqrstuvwxyz',
  appId: '1:123456789012:web:abcdef1234567890',
  messagingSenderId: '123456789012',
  projectId: 'my-y2-project',
  authDomain: 'my-y2-project.firebaseapp.com',
  storageBucket: 'my-y2-project.appspot.com',
  measurementId: 'G-ABCDEF1234',
);
*/
