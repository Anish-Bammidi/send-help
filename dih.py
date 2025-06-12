import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import re
import os

class EventBot:
    def __init__(self, firebase_config_path: str = None):
        """Initialize EventBot with Firebase connection"""
        if not firebase_admin._apps:
            if firebase_config_path:
                cred = credentials.Certificate(firebase_config_path)
                firebase_admin.initialize_app(cred)
            else:
                # Initialize with your Firebase project configuration
                firebase_admin.initialize_app(options={
                    'projectId': 'restaurant-data-backend'
                })
        
        self.db = firestore.client()
        self.ingredient_collection = 'ingredient_inventory'
        self.menu_collection = 'menu'
        
        # Firebase configuration for reference
        self.firebase_config = {
            "apiKey": "AIzaSyAWwy0-N_KMeXF8p5wOCew-OJz9oFQSm5A",
            "authDomain": "restaurant-data-backend.firebaseapp.com",
            "projectId": "restaurant-data-backend",
            "storageBucket": "restaurant-data-backend.firebasestorage.app",
            "messagingSenderId": "1080257817525",
            "appId": "1:1080257817525:web:0b1a9cdb5b8d5abe8d07fc",
            "measurementId": "G-2K3GHNE916"
        }
    
    def process_request(self, json_payload: str) -> Dict[str, Any]:
        """Main entry point for processing Flask backend requests"""
        try:
            data = json.loads(json_payload) if isinstance(json_payload, str) else json_payload
            action = data.get('action', '').lower()
            
            # Route to appropriate handler based on action
            handlers = {
                'plan_event': self.plan_event,
                'check_inventory': self.check_inventory,
                'suggest_menu': self.suggest_menu,
                'dietary_filter': self.filter_by_dietary_requirements,
                'ingredient_substitution': self.suggest_ingredient_substitutions,
                'capacity_check': self.check_event_capacity,
                'expiry_alert': self.check_expiring_ingredients,
                'update_inventory': self.update_inventory_after_event
            }
            
            if action in handlers:
                return handlers[action](data)
            else:
                return self._error_response(f"Unknown action: {action}")
                
        except Exception as e:
            return self._error_response(f"Error processing request: {str(e)}")
    
    def plan_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a complete event with menu suggestions and inventory checks"""
        try:
            guest_count = data.get('guest_count', 0)
            dietary_requirements = data.get('dietary_requirements', [])
            event_date = data.get('event_date', '')
            budget_category = data.get('budget_category', 'medium')  # low, medium, high
            preferred_categories = data.get('preferred_categories', ['Starter', 'Main', 'Dessert'])
            
            # Get available menu items
            menu_items = self._get_menu_items()
            
            # Filter by dietary requirements
            if dietary_requirements:
                menu_items = self._filter_menu_by_dietary(menu_items, dietary_requirements)
            
            # Check ingredient availability
            available_dishes = []
            unavailable_dishes = []
            
            for dish in menu_items:
                availability = self._check_dish_availability(dish, guest_count, event_date)
                if availability['available']:
                    available_dishes.append({
                        **dish,
                        'estimated_cost': self._estimate_dish_cost(dish, guest_count),
                        'missing_ingredients': availability['missing_ingredients']
                    })
                else:
                    unavailable_dishes.append({
                        **dish,
                        'missing_ingredients': availability['missing_ingredients']
                    })
            
            # Create suggested menu by category
            suggested_menu = self._create_balanced_menu(available_dishes, preferred_categories, budget_category)
            
            return {
                'status': 'success',
                'event_plan': {
                    'guest_count': guest_count,
                    'event_date': event_date,
                    'suggested_menu': suggested_menu,
                    'total_estimated_cost': sum(dish.get('estimated_cost', 0) for dish in suggested_menu),
                    'dietary_accommodations': dietary_requirements,
                    'available_alternatives': len(available_dishes),
                    'unavailable_dishes': unavailable_dishes[:5]  # Show first 5 unavailable
                },
                'inventory_alerts': self._get_inventory_alerts(event_date)
            }
            
        except Exception as e:
            return self._error_response(f"Event planning failed: {str(e)}")
    
    def check_inventory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check current inventory status"""
        try:
            ingredient_filter = data.get('ingredients', [])
            check_expiry = data.get('check_expiry', True)
            days_ahead = data.get('days_ahead', 7)
            
            inventory_ref = self.db.collection(self.ingredient_collection)
            
            if ingredient_filter:
                # Check specific ingredients
                inventory_status = {}
                for ingredient in ingredient_filter:
                    doc = inventory_ref.document(ingredient).get()
                    if doc.exists:
                        inventory_status[ingredient] = doc.to_dict()
                    else:
                        inventory_status[ingredient] = {'status': 'not_found'}
            else:
                # Get all inventory
                docs = inventory_ref.stream()
                inventory_status = {doc.id: doc.to_dict() for doc in docs}
            
            # Add expiry analysis if requested
            if check_expiry:
                expiry_alerts = self._analyze_expiry_dates(inventory_status, days_ahead)
            else:
                expiry_alerts = []
            
            return {
                'status': 'success',
                'inventory': inventory_status,
                'expiry_alerts': expiry_alerts,
                'total_items': len(inventory_status),
                'low_stock_items': self._identify_low_stock(inventory_status)
            }
            
        except Exception as e:
            return self._error_response(f"Inventory check failed: {str(e)}")
    
    def suggest_menu(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest menu based on available ingredients and preferences"""
        try:
            guest_count = data.get('guest_count', 1)
            dietary_requirements = data.get('dietary_requirements', [])
            cuisine_preference = data.get('cuisine_preference', '')
            max_dishes = data.get('max_dishes', 10)
            
            # Get menu items
            menu_items = self._get_menu_items()
            
            # Apply filters
            if dietary_requirements:
                menu_items = self._filter_menu_by_dietary(menu_items, dietary_requirements)
            
            if cuisine_preference:
                menu_items = [item for item in menu_items 
                            if cuisine_preference.lower() in item.get('description', '').lower()]
            
            # Check availability and rank by suitability
            suggestions = []
            for dish in menu_items[:max_dishes]:
                availability = self._check_dish_availability(dish, guest_count)
                if availability['available'] or not availability['missing_ingredients']:
                    suitability_score = self._calculate_suitability_score(dish, data)
                    suggestions.append({
                        **dish,
                        'suitability_score': suitability_score,
                        'availability_status': availability,
                        'estimated_prep_time': self._estimate_prep_time(dish, guest_count)
                    })
            
            # Sort by suitability score
            suggestions.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            return {
                'status': 'success',
                'menu_suggestions': suggestions,
                'total_suggestions': len(suggestions),
                'criteria_used': {
                    'guest_count': guest_count,
                    'dietary_requirements': dietary_requirements,
                    'cuisine_preference': cuisine_preference
                }
            }
            
        except Exception as e:
            return self._error_response(f"Menu suggestion failed: {str(e)}")
    
    def filter_by_dietary_requirements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter menu items by dietary requirements"""
        try:
            dietary_requirements = data.get('dietary_requirements', [])
            strict_mode = data.get('strict_mode', True)  # If True, ALL requirements must be met
            
            menu_items = self._get_menu_items()
            filtered_items = self._filter_menu_by_dietary(menu_items, dietary_requirements, strict_mode)
            
            return {
                'status': 'success',
                'filtered_menu': filtered_items,
                'total_matches': len(filtered_items),
                'dietary_requirements': dietary_requirements,
                'strict_mode': strict_mode,
                'categories_available': list(set(item.get('category', 'Unknown') for item in filtered_items))
            }
            
        except Exception as e:
            return self._error_response(f"Dietary filtering failed: {str(e)}")
    
    def suggest_ingredient_substitutions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest ingredient substitutions for unavailable items"""
        try:
            missing_ingredients = data.get('missing_ingredients', [])
            dish_name = data.get('dish_name', '')
            
            substitutions = {}
            inventory_ref = self.db.collection(self.ingredient_collection)
            
            for ingredient in missing_ingredients:
                # Check if ingredient exists and has alternatives
                doc = inventory_ref.document(ingredient).get()
                if doc.exists:
                    ingredient_data = doc.to_dict()
                    alternatives = ingredient_data.get('Alternatives', '').split(',')
                    alternatives = [alt.strip() for alt in alternatives if alt.strip()]
                    
                    # Check availability of alternatives
                    available_alternatives = []
                    for alt in alternatives:
                        alt_doc = inventory_ref.document(alt).get()
                        if alt_doc.exists:
                            alt_data = alt_doc.to_dict()
                            available_alternatives.append({
                                'name': alt,
                                'quantity': alt_data.get('Quantity', 'Unknown'),
                                'type': alt_data.get('Type', 'Unknown'),
                                'expiry': alt_data.get('Expiry', 'Unknown')
                            })
                    
                    substitutions[ingredient] = {
                        'original_status': 'exists_but_insufficient',
                        'alternatives': available_alternatives,
                        'suggestion': self._get_best_substitution(ingredient, available_alternatives)
                    }
                else:
                    # Ingredient doesn't exist, suggest based on common substitutions
                    substitutions[ingredient] = {
                        'original_status': 'not_found',
                        'alternatives': [],
                        'suggestion': self._suggest_common_substitution(ingredient)
                    }
            
            return {
                'status': 'success',
                'dish_name': dish_name,
                'substitutions': substitutions,
                'total_missing': len(missing_ingredients),
                'substitutions_found': len([s for s in substitutions.values() if s['alternatives']])
            }
            
        except Exception as e:
            return self._error_response(f"Substitution suggestion failed: {str(e)}")
    
    def check_event_capacity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if inventory can support event of given size"""
        try:
            guest_count = data.get('guest_count', 0)
            selected_dishes = data.get('selected_dishes', [])
            event_date = data.get('event_date', '')
            
            capacity_analysis = {}
            bottlenecks = []
            total_capacity = float('inf')
            
            for dish_name in selected_dishes:
                dish = self._get_dish_by_name(dish_name)
                if dish:
                    dish_capacity = self._calculate_dish_capacity(dish, event_date)
                    capacity_analysis[dish_name] = dish_capacity
                    
                    if dish_capacity['max_servings'] < guest_count:
                        bottlenecks.append({
                            'dish': dish_name,
                            'max_possible': dish_capacity['max_servings'],
                            'limiting_ingredients': dish_capacity['limiting_ingredients']
                        })
                    
                    total_capacity = min(total_capacity, dish_capacity['max_servings'])
            
            can_accommodate = total_capacity >= guest_count
            
            return {
                'status': 'success',
                'can_accommodate': can_accommodate,
                'max_capacity': int(total_capacity) if total_capacity != float('inf') else 0,
                'requested_guests': guest_count,
                'capacity_analysis': capacity_analysis,
                'bottlenecks': bottlenecks,
                'recommendations': self._get_capacity_recommendations(bottlenecks, guest_count)
            }
            
        except Exception as e:
            return self._error_response(f"Capacity check failed: {str(e)}")
    
    def check_expiring_ingredients(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for ingredients expiring soon"""
        try:
            days_ahead = data.get('days_ahead', 7)
            include_expired = data.get('include_expired', True)
            
            inventory_ref = self.db.collection(self.ingredient_collection)
            docs = inventory_ref.stream()
            
            expiring_soon = []
            expired = []
            current_date = datetime.now().date()
            
            for doc in docs:
                data_dict = doc.to_dict()
                expiry_str = data_dict.get('Expiry', '')
                
                try:
                    expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                    days_until_expiry = (expiry_date - current_date).days
                    
                    ingredient_info = {
                        'name': doc.id,
                        'expiry_date': expiry_str,
                        'days_until_expiry': days_until_expiry,
                        'quantity': data_dict.get('Quantity', 'Unknown'),
                        'type': data_dict.get('Type', 'Unknown')
                    }
                    
                    if days_until_expiry < 0:
                        expired.append(ingredient_info)
                    elif days_until_expiry <= days_ahead:
                        expiring_soon.append(ingredient_info)
                        
                except ValueError:
                    # Invalid date format, skip
                    continue
            
            # Sort by expiry date
            expiring_soon.sort(key=lambda x: x['days_until_expiry'])
            expired.sort(key=lambda x: x['days_until_expiry'], reverse=True)
            
            response = {
                'status': 'success',
                'expiring_soon': expiring_soon,
                'total_expiring_soon': len(expiring_soon),
                'urgent_actions': self._get_expiry_recommendations(expiring_soon)
            }
            
            if include_expired:
                response['expired'] = expired
                response['total_expired'] = len(expired)
            
            return response
            
        except Exception as e:
            return self._error_response(f"Expiry check failed: {str(e)}")
    
    def update_inventory_after_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update inventory quantities after an event"""
        try:
            used_ingredients = data.get('used_ingredients', {})  # {ingredient_name: quantity_used}
            event_name = data.get('event_name', 'Unknown Event')
            
            inventory_ref = self.db.collection(self.ingredient_collection)
            update_log = []
            errors = []
            
            for ingredient_name, quantity_used in used_ingredients.items():
                try:
                    doc_ref = inventory_ref.document(ingredient_name)
                    doc = doc_ref.get()
                    
                    if doc.exists:
                        current_data = doc.to_dict()
                        current_quantity_str = current_data.get('Quantity', '0')
                        
                        # Parse current quantity (assuming format like "5 kg")
                        current_amount, unit = self._parse_quantity(current_quantity_str)
                        used_amount = float(quantity_used)
                        
                        new_amount = max(0, current_amount - used_amount)
                        new_quantity_str = f"{new_amount} {unit}"
                        
                        # Update the document
                        doc_ref.update({'Quantity': new_quantity_str})
                        
                        update_log.append({
                            'ingredient': ingredient_name,
                            'previous_quantity': current_quantity_str,
                            'used_quantity': f"{used_amount} {unit}",
                            'new_quantity': new_quantity_str,
                            'status': 'updated'
                        })
                    else:
                        errors.append(f"Ingredient '{ingredient_name}' not found in inventory")
                        
                except Exception as e:
                    errors.append(f"Failed to update '{ingredient_name}': {str(e)}")
            
            return {
                'status': 'success' if not errors else 'partial_success',
                'event_name': event_name,
                'updates_made': len(update_log),
                'update_log': update_log,
                'errors': errors,
                'low_stock_warnings': self._check_low_stock_after_update(update_log)
            }
            
        except Exception as e:
            return self._error_response(f"Inventory update failed: {str(e)}")
    
    # Helper Methods
    def _get_menu_items(self) -> List[Dict[str, Any]]:
        """Retrieve all menu items from Firestore"""
        menu_ref = self.db.collection(self.menu_collection)
        docs = menu_ref.stream()
        return [doc.to_dict() for doc in docs if doc.exists]
    
    def _get_dish_by_name(self, dish_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific dish by name"""
        menu_ref = self.db.collection(self.menu_collection)
        docs = menu_ref.where('name', '==', dish_name).limit(1).stream()
        for doc in docs:
            return doc.to_dict()
        return None
    
    def _filter_menu_by_dietary(self, menu_items: List[Dict], requirements: List[str], strict: bool = True) -> List[Dict]:
        """Filter menu items by dietary requirements"""
        filtered = []
        for item in menu_items:
            item_tags = item.get('tags', [])
            if strict:
                # All requirements must be met
                if all(req in item_tags for req in requirements):
                    filtered.append(item)
            else:
                # At least one requirement must be met
                if any(req in item_tags for req in requirements):
                    filtered.append(item)
        return filtered
    
    def _check_dish_availability(self, dish: Dict[str, Any], guest_count: int = 1, event_date: str = '') -> Dict[str, Any]:
        """Check if a dish can be prepared for given guest count"""
        ingredients = dish.get('ingredients', [])
        missing_ingredients = []
        available = True
        
        inventory_ref = self.db.collection(self.ingredient_collection)
        
        for ingredient in ingredients:
            doc = inventory_ref.document(ingredient).get()
            if not doc.exists:
                missing_ingredients.append(ingredient)
                available = False
            else:
                ingredient_data = doc.to_dict()
                quantity_str = ingredient_data.get('Quantity', '0')
                amount, _ = self._parse_quantity(quantity_str)
                
                # Rough estimation: assume each dish needs 0.1 units per serving
                required_amount = guest_count * 0.1
                if amount < required_amount:
                    missing_ingredients.append(f"{ingredient} (insufficient quantity)")
                    available = False
        
        return {
            'available': available,
            'missing_ingredients': missing_ingredients
        }
    
    def _parse_quantity(self, quantity_str: str) -> tuple:
        """Parse quantity string like '5 kg' into (amount, unit)"""
        try:
            parts = quantity_str.strip().split()
            if len(parts) >= 2:
                amount = float(parts[0])
                unit = ' '.join(parts[1:])
                return amount, unit
            else:
                return float(parts[0]), 'units'
        except (ValueError, IndexError):
            return 0.0, 'units'
    
    def _estimate_dish_cost(self, dish: Dict[str, Any], guest_count: int) -> float:
        """Estimate cost of preparing dish for given guest count"""
        # Simplified cost estimation based on ingredient count and guest count
        ingredient_count = len(dish.get('ingredients', []))
        base_cost_per_ingredient = 2.0  # Base cost per ingredient
        return ingredient_count * base_cost_per_ingredient * guest_count * 0.1
    
    def _create_balanced_menu(self, available_dishes: List[Dict], preferred_categories: List[str], budget_category: str) -> List[Dict]:
        """Create a balanced menu from available dishes"""
        menu = []
        dishes_by_category = {}
        
        # Group dishes by category
        for dish in available_dishes:
            category = dish.get('category', 'Unknown')
            if category not in dishes_by_category:
                dishes_by_category[category] = []
            dishes_by_category[category].append(dish)
        
        # Select dishes from each preferred category
        max_dishes_per_category = 3 if budget_category == 'high' else 2
        
        for category in preferred_categories:
            if category in dishes_by_category:
                # Sort by cost (ascending for low budget, descending for high budget)
                dishes = dishes_by_category[category]
                if budget_category == 'low':
                    dishes.sort(key=lambda x: x.get('estimated_cost', 0))
                elif budget_category == 'high':
                    dishes.sort(key=lambda x: x.get('estimated_cost', 0), reverse=True)
                
                # Add top dishes from this category
                menu.extend(dishes[:max_dishes_per_category])
        
        return menu
    
    def _get_inventory_alerts(self, event_date: str) -> List[Dict[str, Any]]:
        """Get inventory alerts for event planning"""
        alerts = []
        
        # Check expiring ingredients
        expiry_data = self.check_expiring_ingredients({'days_ahead': 14, 'include_expired': True})
        if expiry_data['status'] == 'success':
            if expiry_data.get('expired'):
                alerts.append({
                    'type': 'expired_ingredients',
                    'severity': 'high',
                    'count': len(expiry_data['expired']),
                    'message': f"{len(expiry_data['expired'])} ingredients have expired"
                })
            
            if expiry_data.get('expiring_soon'):
                alerts.append({
                    'type': 'expiring_soon',
                    'severity': 'medium',
                    'count': len(expiry_data['expiring_soon']),
                    'message': f"{len(expiry_data['expiring_soon'])} ingredients expiring within 14 days"
                })
        
        return alerts
    
    def _calculate_suitability_score(self, dish: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calculate how suitable a dish is based on given criteria"""
        score = 5.0  # Base score
        
        # Bonus for dietary requirements match
        dietary_reqs = criteria.get('dietary_requirements', [])
        dish_tags = dish.get('tags', [])
        matching_tags = len(set(dietary_reqs) & set(dish_tags))
        score += matching_tags * 2
        
        # Bonus for cuisine preference
        cuisine_pref = criteria.get('cuisine_preference', '').lower()
        if cuisine_pref and cuisine_pref in dish.get('description', '').lower():
            score += 3
        
        # Penalty for too many ingredients (complexity)
        ingredient_count = len(dish.get('ingredients', []))
        if ingredient_count > 10:
            score -= (ingredient_count - 10) * 0.5
        
        return max(0, score)
    
    def _estimate_prep_time(self, dish: Dict[str, Any], guest_count: int) -> str:
        """Estimate preparation time for a dish"""
        base_time = len(dish.get('ingredients', [])) * 5  # 5 minutes per ingredient
        guest_factor = max(1, guest_count // 10)  # Extra time for larger groups
        total_minutes = base_time * guest_factor
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
    
    def _analyze_expiry_dates(self, inventory: Dict[str, Dict], days_ahead: int) -> List[Dict[str, Any]]:
        """Analyze expiry dates in inventory"""
        alerts = []
        current_date = datetime.now().date()
        
        for ingredient, data in inventory.items():
            if 'Expiry' in data:
                try:
                    expiry_date = datetime.strptime(data['Expiry'], '%Y-%m-%d').date()
                    days_until_expiry = (expiry_date - current_date).days
                    
                    if days_until_expiry <= days_ahead:
                        alerts.append({
                            'ingredient': ingredient,
                            'expiry_date': data['Expiry'],
                            'days_until_expiry': days_until_expiry,
                            'quantity': data.get('Quantity', 'Unknown'),
                            'urgency': 'high' if days_until_expiry <= 3 else 'medium'
                        })
                except ValueError:
                    continue
        
        return sorted(alerts, key=lambda x: x['days_until_expiry'])
    
    def _identify_low_stock(self, inventory: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Identify low stock items"""
        low_stock = []
        
        for ingredient, data in inventory.items():
            if 'Quantity' in data:
                amount, unit = self._parse_quantity(data['Quantity'])
                # Consider low stock if amount is less than 1 unit
                if amount < 1:
                    low_stock.append({
                        'ingredient': ingredient,
                        'current_quantity': data['Quantity'],
                        'type': data.get('Type', 'Unknown')
                    })
        
        return low_stock
    
    def _calculate_dish_capacity(self, dish: Dict[str, Any], event_date: str = '') -> Dict[str, Any]:
        """Calculate maximum servings possible for a dish"""
        ingredients = dish.get('ingredients', [])
        min_servings = float('inf')
        limiting_ingredients = []
        
        inventory_ref = self.db.collection(self.ingredient_collection)
        
        for ingredient in ingredients:
            doc = inventory_ref.document(ingredient).get()
            if doc.exists:
                ingredient_data = doc.to_dict()
                quantity_str = ingredient_data.get('Quantity', '0')
                amount, _ = self._parse_quantity(quantity_str)
                
                # Assume each serving needs 0.1 units of each ingredient
                possible_servings = int(amount / 0.1)
                if possible_servings < min_servings:
                    min_servings = possible_servings
                    limiting_ingredients = [ingredient]
                elif possible_servings == min_servings:
                    limiting_ingredients.append(ingredient)
            else:
                min_servings = 0
                limiting_ingredients.append(f"{ingredient} (missing)")
                break
        
        return {
            'max_servings': int(min_servings) if min_servings != float('inf') else 0,
            'limiting_ingredients': limiting_ingredients
        }
    
    def _get_capacity_recommendations(self, bottlenecks: List[Dict], guest_count: int) -> List[str]:
        """Get recommendations to increase capacity"""
        recommendations = []
        
        if bottlenecks:
            recommendations.append("Consider purchasing additional ingredients for bottleneck dishes:")
            for bottleneck in bottlenecks[:3]:  # Show top 3 bottlenecks
                recommendations.append(f"- {bottleneck['dish']}: increase {', '.join(bottleneck['limiting_ingredients'])}")
        
        recommendations.append("Alternative solutions:")
        recommendations.append("- Split the event into multiple sessions")
        recommendations.append("- Offer a buffet-style service to reduce portions")
        recommendations.append("- Consider substituting dishes with available alternatives")
        
        return recommendations
    
    def _get_expiry_recommendations(self, expiring_items: List[Dict]) -> List[str]:
        """Get recommendations for handling expiring ingredients"""
        recommendations = []
        
        if not expiring_items:
            return ["No urgent actions needed"]
        
        urgent_items = [item for item in expiring_items if item['days_until_expiry'] <= 2]
        if urgent_items:
            recommendations.append(f"URGENT: Use {len(urgent_items)} ingredients within 2 days:")
            for item in urgent_items[:3]:
                recommendations.append(f"- {item['name']} (expires {item['expiry_date']})")
        
        recommendations.append("General recommendations:")
        recommendations.append("- Plan events using expiring ingredients first")
        recommendations.append("- Consider promotional menus for dishes using expiring items")
        recommendations.append("- Review ordering patterns to reduce waste")
        
        return recommendations
    
    def _get_best_substitution(self, ingredient: str, alternatives: List[Dict]) -> Optional[str]:
        """Get the best substitution from available alternatives"""
        if not alternatives:
            return None
        
        # Simple heuristic: prefer alternatives with more quantity
        best_alt = max(alternatives, key=lambda x: self._parse_quantity(x['quantity'])[0])
        return f"Use {best_alt['name']} instead (available: {best_alt['quantity']})"
    
    def _suggest_common_substitution(self, ingredient: str) -> Optional[str]:
        """Suggest common substitutions for missing ingredients"""
        common_subs = {
            'butter': 'oil or margarine',
            'sugar': 'honey or maple syrup',
            'milk': 'plant-based milk alternatives',
            'eggs': 'flax eggs or applesauce',
            'flour': 'alternative flour types',
            'cream': 'milk with butter or coconut cream'
        }
        
        ingredient_lower = ingredient.lower()
        for key, substitution in common_subs.items():
            if key in ingredient_lower:
                return f"Common substitution: {substitution}"
        
        return "No common substitution found - consider purchasing or omitting"
    
    def _check_low_stock_after_update(self, update_log: List[Dict]) -> List[str]:
        """Check for low stock warnings after inventory update"""
        warnings = []
        
        for update in update_log:
            new_quantity = update['new_quantity']
            amount, unit = self._parse_quantity(new_quantity)
            
            if amount <= 1:
                warnings.append(f"LOW STOCK: {update['ingredient']} now has only {new_quantity}")
            elif amount <= 5:
                warnings.append(f"MODERATE STOCK: {update['ingredient']} has {new_quantity}")
        
        return warnings
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """Generate standardized error response"""
        return {
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }


# Flask Integration Helper Functions
def create_eventbot_app():
    """Create and configure EventBot for Flask integration"""
    try:
        # Initialize EventBot with your Firebase project
        bot = EventBot()
        return bot
    except Exception as e:
        print(f"Failed to initialize EventBot: {e}")
        return None


def handle_flask_request(bot: EventBot, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming Flask requests"""
    try:
        # Convert Flask request to JSON if needed
        if hasattr(request_data, 'get_json'):
            json_data = request_data.get_json()
        else:
            json_data = request_data
        
        # Process the request
        response = bot.process_request(json_data)
        
        # Add metadata
        response['processed_at'] = datetime.now().isoformat()
        response['firebase_project'] = 'restaurant-data-backend'
        
        return response
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Request processing failed: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }


# Example usage and testing functions
def test_eventbot():
    """Test EventBot functionality"""
    print("🔥 Initializing EventBot with Firebase...")
    bot = EventBot()
    
    # Test 1: Check inventory
    print("\n📦 Testing inventory check...")
    inventory_request = {
        'action': 'check_inventory',
        'check_expiry': True,
        'days_ahead': 7
    }
    result = bot.process_request(inventory_request)
    print(f"Inventory check result: {result['status']}")
    
    # Test 2: Plan an event
    print("\n🎉 Testing event planning...")
    event_request = {
        'action': 'plan_event',
        'guest_count': 50,
        'dietary_requirements': ['vegetarian', 'gluten-free'],
        'event_date': '2025-06-20',
        'budget_category': 'medium',
        'preferred_categories': ['Starter', 'Main', 'Dessert']
    }
    result = bot.process_request(event_request)
    print(f"Event planning result: {result['status']}")
    
    # Test 3: Suggest menu
    print("\n🍽️ Testing menu suggestions...")
    menu_request = {
        'action': 'suggest_menu',
        'guest_count': 25,
        'dietary_requirements': ['vegetarian'],
        'cuisine_preference': 'italian',
        'max_dishes': 5
    }
    result = bot.process_request(menu_request)
    print(f"Menu suggestion result: {result['status']}")
    
    # Test 4: Check expiring ingredients
    print("\n⏰ Testing expiry alerts...")
    expiry_request = {
        'action': 'expiry_alert',
        'days_ahead': 10,
        'include_expired': True
    }
    result = bot.process_request(expiry_request)
    print(f"Expiry check result: {result['status']}")
    
    print("\n✅ EventBot testing completed!")
    return bot


# Sample data for testing (you can use this to populate your Firestore)
SAMPLE_INGREDIENT_DATA = {
    'tomatoes': {
        'Quantity': '10 kg',
        'Expiry': '2025-06-20',
        'Type': 'vegetarian',
        'Alternatives': 'cherry tomatoes, canned tomatoes'
    },
    'chicken': {
        'Quantity': '15 kg',
        'Expiry': '2025-06-15',
        'Type': 'meat',
        'Alternatives': 'turkey, beef'
    },
    'flour': {
        'Quantity': '25 kg',
        'Expiry': '2025-08-01',
        'Type': 'vegan',
        'Alternatives': 'almond flour, coconut flour'
    },
    'mozzarella': {
        'Quantity': '8 kg',
        'Expiry': '2025-06-18',
        'Type': 'vegetarian',
        'Alternatives': 'cheddar, vegan cheese'
    },
    'olive_oil': {
        'Quantity': '5 liters',
        'Expiry': '2025-12-31',
        'Type': 'vegan',
        'Alternatives': 'sunflower oil, coconut oil'
    }
}

SAMPLE_MENU_DATA = [
    {
        'name': 'Margherita Pizza',
        'description': 'Classic Italian pizza with tomatoes, mozzarella, and basil',
        'category': 'Main',
        'ingredients': ['tomatoes', 'mozzarella', 'flour', 'olive_oil'],
        'tags': ['vegetarian', 'italian']
    },
    {
        'name': 'Chicken Caesar Salad',
        'description': 'Fresh romaine lettuce with grilled chicken and Caesar dressing',
        'category': 'Main',
        'ingredients': ['chicken', 'lettuce', 'parmesan'],
        'tags': ['protein', 'salad']
    },
    {
        'name': 'Bruschetta',
        'description': 'Toasted bread topped with fresh tomatoes and herbs',
        'category': 'Starter',
        'ingredients': ['tomatoes', 'flour', 'olive_oil'],
        'tags': ['vegetarian', 'italian', 'vegan']
    },
    {
        'name': 'Tiramisu',
        'description': 'Classic Italian dessert with coffee and mascarpone',
        'category': 'Dessert',
        'ingredients': ['mascarpone', 'coffee', 'eggs'],
        'tags': ['vegetarian', 'italian', 'dessert']
    }
]


def populate_sample_data(bot: EventBot):
    """Populate Firestore with sample data for testing"""
    print("📝 Populating sample data...")
    
    try:
        # Add ingredient inventory
        for ingredient_id, data in SAMPLE_INGREDIENT_DATA.items():
            bot.db.collection(bot.ingredient_collection).document(ingredient_id).set(data)
            print(f"✅ Added ingredient: {ingredient_id}")
        
        # Add menu items
        for menu_item in SAMPLE_MENU_DATA:
            bot.db.collection(bot.menu_collection).add(menu_item)
            print(f"✅ Added menu item: {menu_item['name']}")
        
        print("🎉 Sample data populated successfully!")
        
    except Exception as e:
        print(f"❌ Error populating data: {e}")


if __name__ == "__main__":
    # Initialize and test EventBot
    bot = test_eventbot()
    
    # Uncomment the line below to populate sample data
    # populate_sample_data(bot)
