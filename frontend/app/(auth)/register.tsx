import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/auth';
import { api } from '../../src/api';
import { colors, spacing, radius } from '../../src/theme';

const c = colors.light;

export default function RegisterScreen() {
  const router = useRouter();
  const { login } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    if (!name.trim() || !email.trim() || !phone.trim() || !password.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    setLoading(true);
    try {
      const res = await api.register({ name: name.trim(), email: email.trim().toLowerCase(), phone: phone.trim(), password });
      await login(res.token, res.user);
      router.replace('/(tabs)');
    } catch (e: any) {
      Alert.alert('Registration Failed', e.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <TouchableOpacity testID="back-to-login-btn" onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="arrow-back" size={24} color={c.textMain} />
          </TouchableOpacity>

          <View style={styles.header}>
            <Text style={styles.title}>Create Account</Text>
            <Text style={styles.subtitle}>Register your dental clinic</Text>
          </View>

          <View style={styles.formCard}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Full Name</Text>
              <View style={styles.inputWrapper}>
                <Ionicons name="person-outline" size={20} color={c.textMuted} style={styles.inputIcon} />
                <TextInput testID="register-name-input" style={styles.input} placeholder="Dr. Rajesh Sharma" placeholderTextColor={c.textMuted} value={name} onChangeText={setName} />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Email</Text>
              <View style={styles.inputWrapper}>
                <Ionicons name="mail-outline" size={20} color={c.textMuted} style={styles.inputIcon} />
                <TextInput testID="register-email-input" style={styles.input} placeholder="doctor@clinic.com" placeholderTextColor={c.textMuted} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Phone Number</Text>
              <View style={styles.inputWrapper}>
                <Ionicons name="call-outline" size={20} color={c.textMuted} style={styles.inputIcon} />
                <TextInput testID="register-phone-input" style={styles.input} placeholder="+919876543210" placeholderTextColor={c.textMuted} value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Password</Text>
              <View style={styles.inputWrapper}>
                <Ionicons name="lock-closed-outline" size={20} color={c.textMuted} style={styles.inputIcon} />
                <TextInput testID="register-password-input" style={styles.input} placeholder="Create password" placeholderTextColor={c.textMuted} value={password} onChangeText={setPassword} secureTextEntry />
              </View>
            </View>

            <TouchableOpacity testID="register-submit-btn" style={styles.primaryBtn} onPress={handleRegister} disabled={loading} activeOpacity={0.8}>
              {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.primaryBtnText}>Create Account</Text>}
            </TouchableOpacity>
          </View>

          <TouchableOpacity testID="go-login-btn" style={styles.loginLink} onPress={() => router.back()}>
            <Text style={styles.loginLinkText}>Already have an account? <Text style={styles.loginLinkBold}>Sign In</Text></Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: c.background },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, paddingHorizontal: spacing.xl, paddingBottom: spacing.xxxl },
  backBtn: { marginTop: spacing.lg, width: 44, height: 44, justifyContent: 'center' },
  header: { marginTop: spacing.lg, marginBottom: spacing.xxl },
  title: { fontSize: 32, fontWeight: '700', color: c.textMain },
  subtitle: { fontSize: 16, color: c.textMuted, marginTop: spacing.xs },
  formCard: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 12, elevation: 3 },
  inputGroup: { marginBottom: spacing.lg },
  label: { fontSize: 14, fontWeight: '500', color: c.textMuted, marginBottom: spacing.sm },
  inputWrapper: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.background, borderRadius: radius.md, borderWidth: 1, borderColor: c.border, paddingHorizontal: spacing.md },
  inputIcon: { marginRight: spacing.sm },
  input: { flex: 1, paddingVertical: 14, fontSize: 16, color: c.textMain },
  primaryBtn: { backgroundColor: c.primary, borderRadius: radius.full, paddingVertical: 16, alignItems: 'center', marginTop: spacing.lg },
  primaryBtnText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
  loginLink: { alignItems: 'center', marginTop: spacing.xl },
  loginLinkText: { fontSize: 14, color: c.textMuted },
  loginLinkBold: { color: c.primary, fontWeight: '600' },
});
