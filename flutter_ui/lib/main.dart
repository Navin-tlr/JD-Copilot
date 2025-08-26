import 'package:flutter/material.dart';
import 'onboarding_screen.dart'; // Import your new screen
import 'custom_transitions.dart'; // Import custom transitions
import 'firebase_config.dart'; // Import Firebase configuration

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FirebaseConfig.initializeFirebase();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Y^2 App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        pageTransitionsTheme: PageTransitionsTheme(
          builders: {
            TargetPlatform.android: FigmaInteractionPageTransitionsBuilder(),
            TargetPlatform.iOS: FigmaInteractionPageTransitionsBuilder(),
            TargetPlatform.macOS: FigmaInteractionPageTransitionsBuilder(),
            TargetPlatform.windows: FigmaInteractionPageTransitionsBuilder(),
            TargetPlatform.linux: FigmaInteractionPageTransitionsBuilder(),
          },
        ),
      ),
      // Set the OnboardingScreen as the home screen
      home: const OnboardingScreen(),
    );
  }
}
