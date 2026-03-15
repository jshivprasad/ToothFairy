import React, { useState, useCallback } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/api';
import { colors, spacing, radius } from '../../src/theme';

const c = colors.light;

export default function ClinicScreen() {
  const router = useRouter();
  const [clinic, setClinic] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<any>({});

  const loadData = useCallback(async () => {
    try {
      const data = await api.getClinic();
      setClinic(data);
      setForm(data);
    } catch (e) {
      console.log('Clinic load error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { loadData(); }, [loadData]));

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await api.updateClinic({
        name: form.name,
        address: form.address,
        city: form.city,
        state: form.state,
        pincode: form.pincode,
        phone: form.phone,
        email: form.email,
        description: form.description,
        fees_min: parseInt(form.fees_min) || 0,
        fees_max: parseInt(form.fees_max) || 0,
        specializations: form.specializations || [],
      });
      setClinic(updated);
      setEditing(false);
      Alert.alert('Success', 'Clinic information updated');
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.loadingView}><ActivityIndicator size="large" color={c.primary} /></View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <Text style={styles.title}>Clinic Profile</Text>
            {!editing ? (
              <TouchableOpacity testID="edit-clinic-btn" style={styles.editBtn} onPress={() => setEditing(true)}>
                <Ionicons name="create-outline" size={20} color={c.primary} />
                <Text style={styles.editBtnText}>Edit</Text>
              </TouchableOpacity>
            ) : (
              <View style={styles.editActions}>
                <TouchableOpacity testID="cancel-edit-btn" style={styles.cancelBtn} onPress={() => { setEditing(false); setForm(clinic); }}>
                  <Text style={styles.cancelBtnText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity testID="save-clinic-btn" style={styles.saveBtn} onPress={handleSave} disabled={saving}>
                  {saving ? <ActivityIndicator color="#FFF" size="small" /> : <Text style={styles.saveBtnText}>Save</Text>}
                </TouchableOpacity>
              </View>
            )}
          </View>

          {/* Clinic Icon */}
          <View style={styles.iconSection}>
            <View style={styles.clinicIcon}>
              <Ionicons name="medical" size={36} color={c.primary} />
            </View>
            <Text style={styles.clinicName}>{form.name || 'Your Clinic'}</Text>
          </View>

          {/* Quick Links */}
          <View style={styles.quickLinks}>
            <TouchableOpacity testID="manage-hours-btn" style={styles.quickLink} onPress={() => router.push('/clinic-hours')}>
              <Ionicons name="time-outline" size={22} color={c.primary} />
              <Text style={styles.quickLinkText}>Manage Hours</Text>
              <Ionicons name="chevron-forward" size={18} color={c.textMuted} />
            </TouchableOpacity>
          </View>

          {/* Form */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Basic Information</Text>
            <FieldRow label="Clinic Name" value={form.name} field="name" editing={editing} form={form} setForm={setForm} />
            <FieldRow label="Phone" value={form.phone} field="phone" editing={editing} form={form} setForm={setForm} keyboardType="phone-pad" />
            <FieldRow label="Email" value={form.email} field="email" editing={editing} form={form} setForm={setForm} keyboardType="email-address" />
            <FieldRow label="Description" value={form.description} field="description" editing={editing} form={form} setForm={setForm} multiline />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Address</Text>
            <FieldRow label="Address" value={form.address} field="address" editing={editing} form={form} setForm={setForm} />
            <FieldRow label="City" value={form.city} field="city" editing={editing} form={form} setForm={setForm} />
            <FieldRow label="State" value={form.state} field="state" editing={editing} form={form} setForm={setForm} />
            <FieldRow label="Pincode" value={form.pincode} field="pincode" editing={editing} form={form} setForm={setForm} keyboardType="number-pad" />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Fees Range (INR)</Text>
            <View style={styles.feesRow}>
              <View style={styles.feeField}>
                <Text style={styles.label}>Minimum</Text>
                {editing ? (
                  <TextInput testID="fees-min-input" style={styles.input} value={String(form.fees_min || '')} onChangeText={(v) => setForm({ ...form, fees_min: v })} keyboardType="number-pad" />
                ) : (
                  <Text style={styles.fieldValue}>₹{form.fees_min || 0}</Text>
                )}
              </View>
              <View style={styles.feeField}>
                <Text style={styles.label}>Maximum</Text>
                {editing ? (
                  <TextInput testID="fees-max-input" style={styles.input} value={String(form.fees_max || '')} onChangeText={(v) => setForm({ ...form, fees_max: v })} keyboardType="number-pad" />
                ) : (
                  <Text style={styles.fieldValue}>₹{form.fees_max || 0}</Text>
                )}
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function FieldRow({ label, value, field, editing, form, setForm, keyboardType, multiline }: any) {
  return (
    <View style={fieldStyles.row}>
      <Text style={fieldStyles.label}>{label}</Text>
      {editing ? (
        <TextInput
          testID={`clinic-${field}-input`}
          style={[fieldStyles.input, multiline && fieldStyles.multiline]}
          value={form[field] || ''}
          onChangeText={(v) => setForm({ ...form, [field]: v })}
          keyboardType={keyboardType}
          multiline={multiline}
          numberOfLines={multiline ? 3 : 1}
        />
      ) : (
        <Text style={fieldStyles.value}>{value || '-'}</Text>
      )}
    </View>
  );
}

const fieldStyles = StyleSheet.create({
  row: { marginBottom: spacing.lg },
  label: { fontSize: 13, fontWeight: '500', color: c.textMuted, marginBottom: spacing.xs },
  input: { backgroundColor: c.background, borderRadius: radius.md, borderWidth: 1, borderColor: c.border, paddingHorizontal: spacing.md, paddingVertical: 12, fontSize: 16, color: c.textMain },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  value: { fontSize: 16, color: c.textMain },
});

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: c.background },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scroll: { paddingHorizontal: spacing.xl, paddingBottom: 100 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: spacing.lg, paddingBottom: spacing.xl },
  title: { fontSize: 28, fontWeight: '700', color: c.textMain },
  editBtn: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
  editBtnText: { fontSize: 16, color: c.primary, fontWeight: '500' },
  editActions: { flexDirection: 'row', gap: spacing.sm },
  cancelBtn: { paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, borderRadius: radius.full, borderWidth: 1, borderColor: c.border },
  cancelBtnText: { fontSize: 14, color: c.textMuted },
  saveBtn: { paddingHorizontal: spacing.xl, paddingVertical: spacing.sm, borderRadius: radius.full, backgroundColor: c.primary },
  saveBtnText: { fontSize: 14, color: '#FFF', fontWeight: '600' },
  iconSection: { alignItems: 'center', marginBottom: spacing.xxl },
  clinicIcon: { width: 72, height: 72, borderRadius: 36, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  clinicName: { fontSize: 22, fontWeight: '700', color: c.textMain },
  quickLinks: { backgroundColor: c.surface, borderRadius: radius.lg, marginBottom: spacing.xxl, borderWidth: 1, borderColor: c.border, overflow: 'hidden' },
  quickLink: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, paddingVertical: spacing.lg, gap: spacing.md },
  quickLinkText: { flex: 1, fontSize: 16, fontWeight: '500', color: c.textMain },
  section: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, marginBottom: spacing.xl, borderWidth: 1, borderColor: c.border },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: c.textMain, marginBottom: spacing.lg },
  feesRow: { flexDirection: 'row', gap: spacing.lg },
  feeField: { flex: 1 },
  label: { fontSize: 13, fontWeight: '500', color: c.textMuted, marginBottom: spacing.xs },
  input: { backgroundColor: c.background, borderRadius: radius.md, borderWidth: 1, borderColor: c.border, paddingHorizontal: spacing.md, paddingVertical: 12, fontSize: 16, color: c.textMain },
  fieldValue: { fontSize: 20, fontWeight: '600', color: c.primary },
});
