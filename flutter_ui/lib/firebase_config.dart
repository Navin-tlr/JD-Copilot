import 'package:firebase_core/firebase_core.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'firebase_options.dart';

class FirebaseConfig {
  static Future<void> initializeFirebase() async {
    try {
      // Initialize Firebase with the generated configuration
      await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      );
      print('Firebase initialized successfully with generated configuration');
    } catch (e) {
      print('Firebase initialization error: $e');
      rethrow; // Re-throw the error so we can handle it properly
    }
  }

  // Get Firebase Auth instance
  static FirebaseAuth get auth => FirebaseAuth.instance;
  
  // Get Firestore instance
  static FirebaseFirestore get firestore => FirebaseFirestore.instance;
  
  // Get Firebase Storage instance
  static FirebaseStorage get storage => FirebaseStorage.instance;
}
