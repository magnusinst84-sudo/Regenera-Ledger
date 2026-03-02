# Firestore Database Schema

## Collections & Document Structure

### `users`
```
users/{userId}
├── email: string
├── password_hash: string
├── name: string
├── role: "company" | "farmer"
├── company_name: string (optional, for company role)
├── created_at: timestamp
```

### `esg_reports`
```
esg_reports/{reportId}
├── user_id: string (ref → users)
├── filename: string
├── extracted_text: string
├── uploaded_at: timestamp
```

### `scope3_documents`
```
scope3_documents/{docId}
├── user_id: string (ref → users)
├── esg_report_id: string (ref → esg_reports)
├── filename: string
├── extracted_text: string
├── uploaded_at: timestamp
```

### `analysis_results`
```
analysis_results/{resultId}
├── user_id: string (ref → users)
├── esg_report_id: string (ref → esg_reports, optional)
├── analysis_type: "esg" | "scope3" | "carbon_gap"
├── result_json: map (full Gemini output)
├── created_at: timestamp
```

### `farmer_profiles`
```
farmer_profiles/{profileId}
├── user_id: string (ref → users)
├── land_size_hectares: number
├── crop_type: string
├── soil_practices: string
├── irrigation_type: string
├── regenerative_practices: string
├── location: { lat: number, lng: number, name: string }
├── created_at: timestamp
├── updated_at: timestamp
```

### `carbon_estimations`
```
carbon_estimations/{estimationId}
├── farmer_id: string (ref → farmer_profiles)
├── sequestration_capacity_tons: number
├── credibility_score: number (0–100)
├── yearly_credit_potential: number
├── explanation: string
├── result_json: map (full Gemini output)
├── created_at: timestamp
```

### `matching_results`
```
matching_results/{matchId}
├── company_user_id: string (ref → users)
├── carbon_gap: number
├── matches_json: array of maps
├── created_at: timestamp
```

### `audit_logs`
```
audit_logs/{logId}
├── user_id: string (ref → users)
├── action: string
├── entity_type: string
├── entity_id: string
├── details: map
├── created_at: timestamp
```

## Firestore Indexes (create in Firebase Console or `firestore.indexes.json`)

- `esg_reports` → composite: (user_id ASC, uploaded_at DESC)
- `analysis_results` → composite: (user_id ASC, created_at DESC)
- `analysis_results` → composite: (user_id ASC, analysis_type ASC, created_at DESC)
- `audit_logs` → composite: (user_id ASC, created_at DESC)
- `carbon_estimations` → composite: (farmer_id ASC, created_at DESC)
- `matching_results` → composite: (company_user_id ASC, created_at DESC)
