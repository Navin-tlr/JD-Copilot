import 'package:flutter/material.dart';
import 'onboarding_screen.dart'; // Import your new screen

void main() {
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
      ),
      // Set the OnboardingScreen as the home screen
      home: const OnboardingScreen(),
    );
  }
}
