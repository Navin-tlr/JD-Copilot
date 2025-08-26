// flutter_ui/lib/create_account_screen.dart

import 'package:flutter/material.dart';
import 'specialization_screen.dart';
import 'custom_transitions.dart';

class CreateAccountScreen extends StatelessWidget {
  const CreateAccountScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Background Image
          Container(
            decoration: const BoxDecoration(
              image: DecorationImage(
                image: AssetImage(
                    'assets/images/background_landscape.jpg'), // Ensure this is the correct path
                fit: BoxFit.cover,
              ),
            ),
          ),
          // Y logo at the top right
          const Positioned(
            top: 26,
            right: 29,
            child: Text(
              'Y',
              style: TextStyle(
                fontFamily: 'Mogia',
                fontSize: 64,
                fontWeight: FontWeight.w400,
                color: Colors.white,
              ),
            ),
          ),
          // Centered content
          Center(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 29.0),
                child: _CreateAccountCard(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CreateAccountCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 335,
      padding: const EdgeInsets.all(25.0),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.25),
            blurRadius: 4,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'Create \naccount',
            style: TextStyle(
              fontFamily: 'PP Mondwest',
              fontSize: 55,
              fontWeight: FontWeight.w400,
              height: 0.9,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 50),
          const _CustomTextField(hintText: 'How you like to be called?'),
          const SizedBox(height: 12),
          const _CustomTextField(hintText: 'Year of study'),
          const SizedBox(height: 12),
          const _CustomTextField(hintText: 'Christ Mail ID'),
          const SizedBox(height: 12),
          const _CustomTextField(hintText: 'Password', obscureText: true),
          const SizedBox(height: 35),
          _CreateAccountButton(),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

class _CustomTextField extends StatelessWidget {
  final String hintText;
  final bool obscureText;

  const _CustomTextField(
      {required this.hintText, this.obscureText = false});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 54,
      child: TextField(
        obscureText: obscureText,
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: TextStyle(
            fontFamily: 'PP NeueBit',
            fontSize: 20.96,
            fontWeight: FontWeight.w700,
            color: Colors.black.withOpacity(0.6),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(5),
            borderSide: BorderSide(
              color: const Color(0xFF646262).withOpacity(0.6),
              width: 1,
            ),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(5),
            borderSide: const BorderSide(
              color: Color(0xFF613DB9),
              width: 1.5,
            ),
          ),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        ),
      ),
    );
  }
}

class _CreateAccountButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        Navigator.of(context).push(
          GentleFadeRoute(builder: (context) => const SpecializationScreen()),
        );
      },
      child: Container(
        width: 276,
        height: 54,
        decoration: BoxDecoration(
          color: const Color(0xFF613DB9).withOpacity(0.7),
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
            'Create Account',
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
