import React from 'react';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFnsV3';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';

function Field({ label, name, value, onChange, type = 'text', multiline = false }) {
  const base = 'w-full px-3 py-2.5 border border-linen-300 rounded-md bg-white font-sans text-sm text-ink-900 placeholder-ink-300 focus:outline-none focus:border-bronze-400 transition-colors';
  return (
    <div>
      <label htmlFor={`field-${name}`} className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-1">
        {label}
      </label>
      {multiline ? (
        <textarea
          id={`field-${name}`}
          name={name}
          value={value || ''}
          onChange={onChange}
          rows={3}
          className={`${base} resize-none`}
        />
      ) : (
        <input
          id={`field-${name}`}
          type={type}
          name={name}
          value={value || ''}
          onChange={onChange}
          className={base}
        />
      )}
    </div>
  );
}

function Checkbox({ label, name, checked, onChange }) {
  return (
    <label className="flex items-center gap-2.5 cursor-pointer group">
      <input
        type="checkbox"
        name={name}
        checked={checked || false}
        onChange={onChange}
        className="w-4 h-4 border border-linen-300 rounded accent-bronze-500 cursor-pointer"
      />
      <span className="font-sans text-sm text-ink-700 group-hover:text-ink-900 transition-colors">
        {label}
      </span>
    </label>
  );
}

function SectionCard({ title, children }) {
  return (
    <div className="rounded-lg border border-linen-200 p-5 space-y-3">
      <h3 className="font-serif text-lg text-ink-800 mb-1">{title}</h3>
      {children}
    </div>
  );
}

function MissingDetails({ propertyData, onDataChange }) {
  const handleInputChange = (event) => {
    const { name, value, type, checked } = event.target;
    onDataChange({ [name]: type === 'checkbox' ? checked : value });
  };

  const handleFeatureChange = (event) => {
    const { name, value, type, checked } = event.target;
    onDataChange({
      features: {
        ...propertyData.features,
        [name]: type === 'checkbox' ? checked : value,
      },
    });
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <div>
        <h2 className="font-serif text-2xl text-ink-900 mb-5">Property Details</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SectionCard title="Location">
            <Field label="Formatted Address" name="formatted_address" value={propertyData.formatted_address} onChange={handleInputChange} />
            <Field label="Address Line 1" name="address_line1" value={propertyData.address_line1} onChange={handleInputChange} />
            <Field label="Address Line 2" name="address_line2" value={propertyData.address_line2} onChange={handleInputChange} />
            <Field label="City" name="city" value={propertyData.city} onChange={handleInputChange} />
            <Field label="State" name="state" value={propertyData.state} onChange={handleInputChange} />
            <Field label="Zip Code" name="zip_code" value={propertyData.zip_code} onChange={handleInputChange} />
            <Field label="County" name="county" value={propertyData.county} onChange={handleInputChange} />
            <Field label="Latitude" name="latitude" value={propertyData.latitude} onChange={handleInputChange} type="number" />
            <Field label="Longitude" name="longitude" value={propertyData.longitude} onChange={handleInputChange} type="number" />
          </SectionCard>

          <SectionCard title="Characteristics">
            <Field label="Property Type" name="property_type" value={propertyData.property_type} onChange={handleInputChange} />
            <Field label="Bedrooms" name="bedrooms" value={propertyData.bedrooms} onChange={handleInputChange} type="number" />
            <Field label="Bathrooms" name="bathrooms" value={propertyData.bathrooms} onChange={handleInputChange} type="number" />
            <Field label="Square Footage" name="square_footage" value={propertyData.square_footage} onChange={handleInputChange} type="number" />
            <Field label="Lot Size" name="lot_size" value={propertyData.lot_size} onChange={handleInputChange} type="number" />
            <Field label="Year Built" name="year_built" value={propertyData.year_built} onChange={handleInputChange} type="number" />
            <Field label="Assessor ID" name="assessor_id" value={propertyData.assessor_id} onChange={handleInputChange} />
            <Field label="Legal Description" name="legal_description" value={propertyData.legal_description} onChange={handleInputChange} multiline />
            <Field label="Subdivision" name="subdivision" value={propertyData.subdivision} onChange={handleInputChange} />
            <Field label="Zoning" name="zoning" value={propertyData.zoning} onChange={handleInputChange} />
          </SectionCard>

          <SectionCard title="Sale Information">
            <div>
              <label className="block font-sans text-xs uppercase tracking-widest text-ink-400 mb-1">
                Last Sale Date
              </label>
              <DatePicker
                value={propertyData.last_sale_date ? new Date(propertyData.last_sale_date) : null}
                onChange={(val) => onDataChange({ last_sale_date: val })}
                slotProps={{
                  textField: {
                    size: 'small',
                    fullWidth: true,
                    sx: {
                      '& .MuiOutlinedInput-root': {
                        fontFamily: 'DM Sans, sans-serif',
                        fontSize: '0.875rem',
                        borderRadius: '0.375rem',
                        '& fieldset': { borderColor: '#DDD8D0' },
                        '&:hover fieldset': { borderColor: '#B89A78' },
                        '&.Mui-focused fieldset': { borderColor: '#8B7355' },
                      },
                    },
                  },
                }}
              />
            </div>
            <Field label="Last Sale Price" name="last_sale_price" value={propertyData.last_sale_price} onChange={handleInputChange} type="number" />
            <Checkbox label="Owner Occupied" name="owner_occupied" checked={propertyData.owner_occupied} onChange={handleInputChange} />
          </SectionCard>

          <SectionCard title="Features">
            <Field label="Architecture Type" name="architecture_type" value={propertyData.features?.architecture_type} onChange={handleFeatureChange} />
            <Checkbox label="Cooling" name="cooling" checked={propertyData.features?.cooling} onChange={handleFeatureChange} />
            <Field label="Cooling Type" name="cooling_type" value={propertyData.features?.cooling_type} onChange={handleFeatureChange} />
            <Field label="Exterior Type" name="exterior_type" value={propertyData.features?.exterior_type} onChange={handleFeatureChange} />
            <Field label="Floor Count" name="floor_count" value={propertyData.features?.floor_count} onChange={handleFeatureChange} type="number" />
            <Field label="Foundation Type" name="foundation_type" value={propertyData.features?.foundation_type} onChange={handleFeatureChange} />
            <Checkbox label="Garage" name="garage" checked={propertyData.features?.garage} onChange={handleFeatureChange} />
            <Field label="Garage Type" name="garage_type" value={propertyData.features?.garage_type} onChange={handleFeatureChange} />
            <Checkbox label="Heating" name="heating" checked={propertyData.features?.heating} onChange={handleFeatureChange} />
            <Field label="Heating Type" name="heating_type" value={propertyData.features?.heating_type} onChange={handleFeatureChange} />
            <Checkbox label="Pool" name="pool" checked={propertyData.features?.pool} onChange={handleFeatureChange} />
            <Field label="Roof Type" name="roof_type" value={propertyData.features?.roof_type} onChange={handleFeatureChange} />
            <Field label="Room Count" name="room_count" value={propertyData.features?.room_count} onChange={handleFeatureChange} type="number" />
            <Field label="Unit Count" name="unit_count" value={propertyData.features?.unit_count} onChange={handleFeatureChange} type="number" />
          </SectionCard>
        </div>
      </div>
    </LocalizationProvider>
  );
}

export default MissingDetails;
