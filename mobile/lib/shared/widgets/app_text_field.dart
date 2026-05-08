import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

class AppTextField extends StatelessWidget {
  final TextEditingController? controller;
  final String label;
  final String hint;
  final IconData? prefixIcon;
  final Widget? suffixIcon;
  final bool obscureText;
  final TextInputType keyboardType;
  final String? Function(String?)? validator;

  const AppTextField({
    super.key,
    this.controller,
    required this.label,
    required this.hint,
    this.prefixIcon,
    this.suffixIcon,
    this.obscureText = false,
    this.keyboardType = TextInputType.text,
    this.validator,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller:   controller,
      obscureText:  obscureText,
      keyboardType: keyboardType,
      validator:    validator,
      style:        const TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
      decoration: InputDecoration(
        labelText:    label,
        hintText:     hint,
        prefixIcon:   prefixIcon != null ? Icon(prefixIcon, color: AppTheme.greenDark) : null,
        suffixIcon:   suffixIcon,
        labelStyle:   const TextStyle(color: Colors.grey),
        floatingLabelStyle: const TextStyle(color: AppTheme.greenDark),
      ),
    );
  }
}
