// flutter_ui/lib/onboarding_screen.dart

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'create_account_screen.dart';
import 'custom_transitions.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const SizedBox(height: 60),
                // New Y² Logo
                Image.asset(
                  'assets/images/y_logo.png', // Make sure the new logo is at this path
                  width: 109,
                  height: 104,
                ),
                const SizedBox(height: 22),
                // Welcome Text
                const Text(
                  'Welcome to Y²',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.black,
                    fontSize: 48,
                    fontFamily: 'PP Mondwest',
                    fontWeight: FontWeight.w400,
                  ),
                ),
                const SizedBox(height: 30),
                // Feature Sections
                _FeatureDetail(
                  iconPath: 'assets/images/new_model_icon.svg', // Updated
                  title: 'RAG powered JD-queries',
                  description:
                      'Ask smarter questions about job opportunities. Get data on past recruiters, salaries, skills in demand, and specialization-wise trends, even compare JDs across companies.',
                ),
                const SizedBox(height: 35),
                _FeatureDetail(
                  iconPath: 'assets/images/doc_ai_icon.svg', // Updated
                  title: 'Strategize your Resume',
                  description:
                      'Check ATS compatibility and get instant resume scores. Uncover skill gaps with targeted certification suggestions. Build role-based versions and boost impact with smart insights.',
                ),
                const SizedBox(height: 35),
                _FeatureDetail(
                  iconPath: 'assets/images/visual_recognition_icon.svg', // Updated
                  title: 'Radar & Deep Research',
                  description:
                      'Command the field with a constant stream of intelligence, Business trends, GD topics, and shifting skills drawn from LinkedIn APIs, News APIs, Reddit, and Twitter APIs.',
                ),
                const SizedBox(height: 50),
                // Get Started Button
                _GetStartedButton(),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// Reusable widget for feature details
class _FeatureDetail extends StatelessWidget {
  final String iconPath;
  final String title;
  final String description;

  const _FeatureDetail({
    required this.iconPath,
    required this.title,
    required this.description,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SvgPicture.asset(iconPath, width: 48, height: 48),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  color: Colors.black,
                  fontSize: 26.29,
                  fontFamily: 'PP NeueBit',
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                description,
                style: const TextStyle(
                  color: Colors.black,
                  fontSize: 10,
                  fontFamily: 'SF Pro',
                  fontWeight: FontWeight.w100,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// Widget for the 'Get Started' button
class _GetStartedButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        Navigator.of(context).push(
          FigmaInteractionRoute(builder: (context) => const CreateAccountScreen()),
        );
      },
      child: Container(
        width: 276,
        height: 54,
        decoration: BoxDecoration(
          color: const Color(0xFF613DB9).withOpacity(0.70),
          borderRadius: BorderRadius.circular(5),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.25),
              blurRadius: 4,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: const Center(
          child: Text(
            'Get started',
            style: TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontFamily: 'PP NeueBit',
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }
}