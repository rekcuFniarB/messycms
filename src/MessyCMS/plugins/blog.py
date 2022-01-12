from MessyCMS import plugins
from MessyCMS.models import Node
import math

## Items list with cursor type pagination (like on Reddit)

class ItemslistCursorPaginated(plugins.ItemsList):
    def execute(self, node, request=None, *args, **kwargs):
        result = {
            'templates': plugins.templates(node, request),
            'context': {
                'nodes': None,
                'node': node,
                'next_page': None,
                'prev_page': None,
                'last_page': None,
                'first_page': None
            }
        }
        
        if node.link:
            items = node.link.get_descendants()
        else:
            ## Using parent if no link defined
            items = node.parent.parent.get_descendants()
        
        items = items.filter(available=True, type='content', parent__type='content')
        
        ## If node has "filter" property
        prop_filter = node.prop('filter')
        if type(prop_filter) is dict:
            items = items.filter(**prop_filter)
        
        prop_order = node.prop('order', ['-ts_created', '-id'])
        if type(prop_order) is str:
            prop_order = [prop_order]
        
        items = items.order_by(*prop_order)
        
        limit = int(node.prop('limit', 10))
        
        if limit:
            try:
                node_id = int(request.GET.get('page', 0))
            except:
                node_id = 0
            
            sliced = items
            
            current_node = Node.objects.filter(id=node_id).first()
            if current_node:
                filter_kwargs = {}
                for _ in prop_order:
                    k = _.strip('-')
                    if _.startswith('-'):
                        filter_kwargs[f'{k}__lte'] = getattr(current_node, k)
                    else:
                        filter_kwargs[f'{k}__gte'] = getattr(current_node, k)
                ## Current node plus slice of nodes older than selected node
                #sliced = sliced.filter(ts_created__lte=current_node.ts_created)
                sliced = sliced.filter(**filter_kwargs)
            
            ## Nodes for current page + first node of next page
            sliced = sliced[:limit + 1]
            ## Current page nodes only
            result['context']['nodes'] = sliced[:limit]
            
            ## There is next page
            if sliced.count() > limit:
                ## Getting first item of next page.
                ## It's not possible to use .last(), it fails with error
                ## "Cannot reverse a query once a slice has been taken".
                result['context']['next_page'] = sliced[limit]
                
                ## Get last page link
                result['context']['last_page'] = items[ math.ceil(items.count() / limit) * limit - limit : ][0]
                
                if result['context']['last_page'].id == result['context']['next_page'].id:
                    # Not showing next page link if next is last page.
                    result['context']['next_page'] = None
            
            ## Checkout if there is prev page
            if current_node:
                filter_kwargs = {}
                for _ in prop_order:
                    k = _.strip('-')
                    if _.startswith('-'):
                        filter_kwargs[f'{k}__gt'] = getattr(current_node, k)
                    else:
                        filter_kwargs[f'{k}__lt'] = getattr(current_node, k)
                #sliced = items.filter(ts_created__gt=current_node.ts_created)
                sliced = items.filter(**filter_kwargs)
                if sliced:
                    if sliced.count() > limit:
                        result['context']['prev_page'] = sliced[sliced.count() - limit:][0]
                    
                    result['context']['first_page'] = True
        
        node.context.update(result['context'])
        return result
